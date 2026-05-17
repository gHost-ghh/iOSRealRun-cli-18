import inspect

import logging
import multiprocessing

from pymobiledevice3.lockdown import create_using_usbmux, LockdownClient

try:
    from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
except ImportError:
    from pymobiledevice3.cli.remote import RemoteServiceDiscoveryService

try:
    from pymobiledevice3.remote.module_imports import start_tunnel, verify_tunnel_imports
except ImportError:
    from pymobiledevice3.cli.remote import start_tunnel, verify_tunnel_imports

from pymobiledevice3.services.amfi import AmfiService

from pymobiledevice3.exceptions import NoDeviceConnectedError

async def maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value

async def get_usbmux_lockdownclient():
    while True:
        try:
            lockdown = await maybe_await(create_using_usbmux())
        except NoDeviceConnectedError:
            print("请连接设备后按回车...")
            input()
        else:
            break

    while True:
        lockdown = await maybe_await(create_using_usbmux())
        if lockdown.all_values.get("PasswordProtected"):
            print("请解锁设备后按回车...")
            input()
        else:
            break

    return lockdown

def get_version(lockdown: LockdownClient):
    return lockdown.all_values.get("ProductVersion")

async def get_developer_mode_status(lockdown: LockdownClient):
    if hasattr(lockdown, "get_developer_mode_status"):
        return await maybe_await(lockdown.get_developer_mode_status())

    return lockdown.developer_mode_status

async def reveal_developer_mode(lockdown: LockdownClient):
    return await maybe_await(
        AmfiService(lockdown).reveal_developer_mode_option_in_ui()
    )


async def enable_developer_mode(lockdown: LockdownClient):
    return await maybe_await(
        AmfiService(lockdown).enable_developer_mode()
    )
async def tunnel(rsd: RemoteServiceDiscoveryService, queue: multiprocessing.Queue):
    if not verify_tunnel_imports():
        raise RuntimeError("pymobiledevice3 tunnel 相关依赖导入失败")

    async with start_tunnel(rsd, secrets=None) as tunnel_result:
        queue.put((tunnel_result.address, tunnel_result.port))
        await tunnel_result.client.wait_closed()