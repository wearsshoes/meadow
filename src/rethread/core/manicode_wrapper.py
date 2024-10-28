"""
Beta version of a Manicode wrapper using PTY to execute Manicode commands.
"""

import os
import select
from typing import Dict
import asyncio
import ptyprocess


async def execute_manicode(instructions: str, options: Dict[str, str]) -> str:
    """Execute a Manicode command using PTY"""
    output = ""
    shell = "bash"  # Assuming Unix-like system since PTY is required
    pty = None

    try:
        pty = ptyprocess.PtyProcess.spawn([shell], env=os.environ, cwd=options["cwd"])
        last_read = asyncio.get_event_loop().time()
        pty.write(f'manicode . "{instructions}"\r'.encode())

        while True:
            current_time = asyncio.get_event_loop().time()
            time_since_last_read = current_time - last_read

            if not pty.isalive():
                break

            if time_since_last_read > 30: # Unconditional timeout
                break

            if time_since_last_read > 10 and "Wait..." not in output and "file:" not in output:
                break

            if not select.select([pty.fd], [], [], 0.1)[0]:
                await asyncio.sleep(0)
                continue

            try:
                data = pty.read()
            except (ptyprocess.PtyProcessError):
                break

            if not data:
                continue

            decoded = data.decode()
            output += decoded
            print(decoded, end="", flush=True)
            last_read = current_time

            if "Complete!" in output:
                break

            await asyncio.sleep(0)

    finally:
        if pty and pty.isalive():
            pty.terminate()

    return output


async def test():
    """Test function"""
    project_root = os.path.join(os.getcwd(), "static")
    try:
        result = await execute_manicode(
            "add dark mode responsive to system settings", {"cwd": project_root}
        )
        print("\nFinal result:", result)
    except (OSError, ptyprocess.PtyProcessError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())