"""
Beta version of a Manicode wrapper using PTY to execute Manicode commands.
"""

import os
import select
from typing import Dict
import asyncio
import ptyprocess


async def execute_manicode(instructions: str, options: Dict[str, str], allow_notes: bool = False) -> str:
    """Execute a Manicode command using PTY

    Args:
        instructions: The instructions for Manicode
        options: Dictionary of options including cwd
        allow_notes: Whether to grant access to notes directory
    """
    output = ""
    shell = "bash"  # Assuming Unix-like system since PTY is required
    pty = None

    try:
        print("[DEBUG] Starting manicode process...")
        env = os.environ.copy()
        if allow_notes:
            env["MANICODE_ALLOW_NOTES"] = "1"
            env["MANICODE_NOTES_DIR"] = options.get("notes_dir", "")
            print(f"[DEBUG] Notes enabled: {env['MANICODE_NOTES_DIR']}")
        pty = ptyprocess.PtyProcess.spawn([shell], env=env, cwd=options["cwd"])
        print("[DEBUG] Process spawned successfully")
        last_read = asyncio.get_event_loop().time()
        try:
            # Escape quotes and newlines for shell
            escaped_instructions = instructions.replace('"', '\\"').replace('\n', '\\n')
            print("[DEBUG] Writing to PTY (length: {})".format(len(escaped_instructions)))

            # Write command in chunks to avoid buffer overflow
            chunk_size = 1024
            command = f"manicode . '{escaped_instructions}'; exit\r"
            for i in range(0, len(command), chunk_size):
                chunk = command[i:i + chunk_size]
                pty.write(chunk.encode())
                await asyncio.sleep(0.1)  # Give PTY time to process
            print("[DEBUG] Command sent, waiting for output...")
        except ptyprocess.PtyProcessError as e:
            print(f"[ERROR] Failed to write to PTY: {str(e)}")
            raise

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
                await asyncio.sleep(0.1)
                continue

            try:
                data = pty.read()
            except ptyprocess.PtyProcessError as e:
                print(f"[ERROR] PTY process error: {str(e)}")
                break

            if not data:
                continue

            decoded = data.decode()
            output += decoded
            if "Thinking..." in output:
                print(decoded, end="", flush=True)
            last_read = current_time

            if "Complete!" in output:
                break

            await asyncio.sleep(0)

    finally:
        if pty and pty.isalive():
            pty.terminate()

    print("[DEBUG] Manicode process complete")
    return output


async def test():
    """Test function"""
    project_root = os.path.join(os.getcwd(), "src/rethread/web/static")
    try:
        result = await execute_manicode(
            "add dark mode responsive to system settings", {"cwd": project_root}
        )
        print("\nFinal result:", result)
    except (OSError, ptyprocess.PtyProcessError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())