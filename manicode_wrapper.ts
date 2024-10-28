import * as pty from "node-pty";
import * as os from "node:os";
import path from "node:path";

async function executeManicode(
  instructions: string,
  options: {
    cwd: string;
  }
 ): Promise<string> {
  return new Promise((resolve, reject) => {
    let output = "";

    const shell = os.platform() === "win32" ? "powershell.exe" : "bash";

    const ptyProcess = pty.spawn(shell, [], {
      name: "xterm-color",
      cols: 80,
      rows: 30,
      cwd: options.cwd,
      env: process.env,
    });

    ptyProcess.onData((data) => {
      output += data;

      if (output.includes("Complete!")) {
        ptyProcess.kill();
      }
    });

    ptyProcess.write(`manicode . "${instructions}"\r`);

    ptyProcess.onExit(() => {
      resolve(output);
    });
  });
}

async function test() {
  const projectRoot = path.join(process.cwd(), "../template");

  const result = await executeManicode(
    "double the font size of all text on the homepage",
    {
      cwd: projectRoot,
    }
  );

  console.log(result);
}

test();
