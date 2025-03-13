import asyncio
import datetime
import os
import random
from typing import Callable, Dict, Optional, Any, List, Literal

from dotenv import load_dotenv

from viam.rpc.dial import DialOptions, Credentials
from viam.app.viam_client import ViamClient, AppClient
from viam.components.camera import Camera
from viam.errors import ResourceNotFoundError
from viam.services.discovery import DiscoveryClient
from viam.robot.client import RobotClient


# Define valid RTSP stream types
RTSPStreamType = Literal["h264", "h265"]

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_KEY_ID = os.getenv("API_KEY_ID")
PART_ID = os.getenv("PART_ID")
MACHINE_ADDRESS = os.getenv("MACHINE_ADDRESS")
H264_RTSP_ADDR = os.getenv("H264_RTSP_ADDR")
H265_RTSP_ADDR = os.getenv("H265_RTSP_ADDR")


def get_rtsp_address(stream_type: RTSPStreamType = "h264") -> str:
    rtsp_addr = {
        "h264": H264_RTSP_ADDR,
        "h265": H265_RTSP_ADDR
    }.get(stream_type)
    
    if not rtsp_addr:
        raise ValueError(f"Unsupported stream type: {stream_type}")
    
    return rtsp_addr


async def connect() -> ViamClient:
    dial_options = DialOptions(
        credentials=Credentials(
            type="api-key",
            payload=API_KEY,
        ),
        auth_entity=API_KEY_ID,
    )
    return await ViamClient.create_from_dial_options(dial_options)


async def connect_machine() -> RobotClient:
    opts = RobotClient.Options.with_api_key(
        api_key=API_KEY,
        api_key_id=API_KEY_ID,
    )
    return await RobotClient.at_address(MACHINE_ADDRESS, opts)


def config_h2645(rtp_passthrough: bool, stream_type: RTSPStreamType = "h264") -> Dict[str, Any]:
    """
    Configure camera using specified RTSP stream type
    
    Args:
        rtp_passthrough: Whether to enable RTP passthrough
        stream_type: Type of RTSP stream ("h264" or "h265")
    """
    return {
        "components": [
            {
                "name": "rtsp-cam-1",
                "namespace": "rdk",
                "type": "camera",
                "model": "viam:viamrtsp:rtsp",
                "attributes": {
                    "rtp_passthrough": rtp_passthrough,
                    "rtsp_address": get_rtsp_address(stream_type)
                }
            }
        ],
        "modules": [
            {
                "type": "registry",
                "name": "viam_viamrtsp",
                "module_id": "viam:viamrtsp",
                "version": "latest-with-prerelease"
            }
        ]
    }


def config_onvif() -> Dict[str, Any]:
    return {
        "components": [
            {
                "name": "rtsp-cam-1",
                "namespace": "rdk",
                "type": "camera",
                "model": "viam:viamrtsp:rtsp",
                "attributes": {
                    "rtp_passthrough": True,
                    "rtsp_address": get_rtsp_address(2)
                }
            }
        ],
        "services": [
            {
                "name": "onvif-discovery-1",
                "api": "rdk:service:discovery",
                "model": "viam:viamrtsp:onvif",
                "attributes": {}
            }
        ],
        "modules": [
            {
                "type": "registry",
                "name": "viam_viamrtsp",
                "module_id": "viam:viamrtsp",
                "version": "latest-with-prerelease"
            }
        ]
    }


def config_video_store(preset: str) -> Dict[str, Any]:
    return {
        "components": [
            {
                "name": "rtsp-cam-1",
                "namespace": "rdk",
                "type": "camera",
                "model": "viam:viamrtsp:rtsp",
                "attributes": {
                    "rtsp_address": get_rtsp_address(2),
                    "rtp_passthrough": True
                }
            },
            {
                "name": "video-store-1",
                "api": "rdk:component:camera",
                "model": "viam:video:storage",
                "attributes": {
                    "sync": "data-manager-1",
                    "storage": {"size_gb": 1},
                    "video": {
                        "preset": preset
                    },
                    "camera": "rtsp-cam-1"
                },
                "depends_on": [
                    "data-manager-1"
                ]
            }
        ],
        "services": [
            {
                "name": "onvif-discovery-1",
                "api": "rdk:service:discovery",
                "model": "viam:viamrtsp:onvif",
                "attributes": {}
            },
            {
                "name": "data-manager-1",
                "api": "rdk:service:data_manager",
                "model": "rdk:builtin:builtin",
                "attributes": {
                    "tags": [],
                    "additional_sync_paths": [],
                    "sync_interval_mins": 0.1,
                    "capture_dir": ""
                }
            }
        ],
        "modules": [
            {
                "type": "registry",
                "name": "viam_viamrtsp",
                "module_id": "viam:viamrtsp",
                "version": "latest-with-prerelease"
            },
            {
                "type": "registry",
                "name": "viam_video-store",
                "module_id": "viam:video-store",
                "version": "latest"
            }
        ]
    }


async def update_and_confirm(cloud: AppClient, part_id: str, name: str, config: Dict[str, Any], prompt: str) -> None:
    await cloud.update_robot_part(robot_part_id=part_id, name=name, robot_config=config)
    input(prompt)


async def wait_for_resource(machine: RobotClient, resource_getter: Callable[[], Any], resource_name: str) -> Any:
    resource = None
    while not resource:
        try:
            resource = resource_getter()
        except ResourceNotFoundError as e:
            print(f"{resource_name} resource not found yet. Sleeping then trying again. Error: {e}")
            await asyncio.sleep(1)
            await safe_refresh_machine(machine)
    return resource


async def safe_refresh_machine(machine: RobotClient) -> None:
    """
    Safely refresh the machine connection, swallowing and logging any errors.
    """
    try:
        await machine.refresh()
    except Exception as e:
        print(f"Got error while refreshing machine. Continuing anyway. Error: {e}")


async def test_video_store_preset(cloud: AppClient, part_id: str, robot_part_name: str, machine: RobotClient, preset: str, sleep_time: int = 30) -> Camera:
    """Test video-store with a specific preset configuration."""
    print(f"Testing video-store with '{preset}' preset.")
    await update_and_confirm(cloud, part_id, robot_part_name, config_video_store(preset),
                          f"Video-store config updated with {preset} preset. Enter/Return to continue.")
    await safe_refresh_machine(machine)
    
    vid_store: Camera = await wait_for_resource(machine, 
                                     lambda: Camera.from_robot(machine, "video-store-1"),
                                     "video-store-1")
    
    print(f"Connected to video-store, sleeping for {sleep_time} seconds to get some video playback before saving.")
    await asyncio.sleep(sleep_time)
    
    now = datetime.datetime.now().astimezone()
    random_seconds = random.randint(2, min(15, sleep_time-1))
    from_time = now - datetime.timedelta(seconds=random_seconds)
    now_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    from_str = from_time.strftime("%Y-%m-%d_%H-%M-%S")
    
    cmd = {
        "command": "save",
        "from": from_str,
        "to": now_str,
        "metadata": "metadata",
        "async": True,
    }
    print(f"Sending save command. {cmd}")
    await vid_store.do_command(cmd)
    input(f"Verify playback of the saved video with {preset} preset on App now.")
    
    return vid_store


async def main() -> None:
    viam_client = await connect()
    cloud = viam_client.app_client
    part = await cloud.get_robot_part(robot_part_id=PART_ID)

    # Test h264 stream with rtp_passthrough = True
    print("Setting config to have h264 camera with rtp_passthrough.")
    await update_and_confirm(cloud, PART_ID, part.name, config_h2645(True, stream_type="h264"),
                             "Please confirm that the stream works with rtp_passthrough before continuing.")

    # Test h264 stream with rtp_passthrough = False
    print("Cool. Moving onto without passthrough.")
    await update_and_confirm(cloud, PART_ID, part.name, config_h2645(False, stream_type="h264"),
                             "Please confirm that the stream works without rtp_passthrough before continuing.")

    # Test h265 stream with passthrough True
    print("Ok now testing stream with h265.")
    await update_and_confirm(cloud, PART_ID, part.name, config_h2645(True, stream_type="h265"),
                             "Please confirm that the h265 stream works.")

    # Test ONVIF discovery
    print("Okay now we need to test ONVIF discovery")
    await update_and_confirm(cloud, PART_ID, part.name, config_onvif(),
                             "ONVIF config updated. Enter/return to continue.")

    machine = await connect_machine()
    onvif_discovery: DiscoveryClient = await wait_for_resource(machine, lambda: DiscoveryClient.from_robot(machine, "onvif-discovery-1"),
                                              "onvif discovery")
    print("Connected to discovery service. Running discover resources...")
    result = await onvif_discovery.discover_resources()
    print(result)
    input("Verify the above discovery results.")

    # Test video-store with different presets
    print("Okay. Moving onto video-store.")
    vid_store = await test_video_store_preset(cloud, PART_ID, part.name, machine, "medium")
    
    print("Reconfiguring to ultrafast preset and re-testing.")
    await vid_store.close()  # close previous connection before creating a new one
    _ = await test_video_store_preset(cloud, PART_ID, part.name, machine, "ultrafast")

    if viam_client:
        await viam_client.close()
    if machine:
        await machine.close()
    print("All tests ran. byebye")


if __name__ == '__main__':
    asyncio.run(main())
