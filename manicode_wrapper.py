"""Test wrapper for executing manicode commands"""
import os
import platform
from typing import Dict
import asyncio
import ptyprocess

async def execute_manicode(instructions: str, options: Dict[str, str]) -> str:
    """Execute a test manicode command"""
    output = ""

    shell = "powershell.exe" if platform.system() == "Windows" else "bash"

    pty = ptyprocess.PtyProcess.spawn(
        [shell],
        env=os.environ,
        cwd=options["cwd"],
        dimensions=(30, 80)
    )

    pty.write(f'manicode . "{instructions}"\r')

    while pty.isalive():
        try:
            data = pty.read()
            if data:
                output += data.decode()
                if "Complete!" in output:
                    pty.terminate()
                    break
        except EOFError:
            break

    return output

async def test():
    """Test function"""
    project_root = os.path.join(os.getcwd(), "../template")

    result = await execute_manicode(
        "double the font size of all text on the homepage",
        {"cwd": project_root}
    )

    print(result)

if __name__ == "__main__":
    asyncio.run(test())