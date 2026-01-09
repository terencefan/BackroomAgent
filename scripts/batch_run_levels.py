import os
import subprocess
import sys
import time


def run_batch_levels(start, end):
    python_executable = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "run_level_agent.py")
    log_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "tmp", "batch_run.log"
    )

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    with open(log_file, "w") as f:
        f.write(f"Starting batch run for levels {start}-{end}\n")

    for i in range(start, end + 1):
        level_name = f"level-{i}"
        # Construct the URL explicitly to avoid search issues
        level_url = f"https://backrooms-wiki-cn.wikidot.com/{level_name}"

        msg = f"Processing {level_name} ({level_url})..."
        print(msg)
        with open(log_file, "a") as f:
            f.write(msg + "\n")

        try:
            # Using subprocess.run to execute the script for each level
            # passing --force to ensure regeneration
            result = subprocess.run(
                [python_executable, script_path, level_url, "--force"],
                check=True,
                text=True,
                capture_output=True,  # Capture output to avoid terminal flooding
            )
            success_msg = f"Successfully processed {level_name}"
            print(success_msg)
            with open(log_file, "a") as f:
                f.write(success_msg + "\n")
                f.write(result.stdout + "\n")  # Log stdout to file

        except subprocess.CalledProcessError as e:
            error_msg = f"Error processing {level_name}: {e}\n{e.stderr}"
            print(f"Error processing {level_name}")
            with open(log_file, "a") as f:
                f.write(error_msg + "\n")
        except Exception as e:
            error_msg = f"An unexpected error occurred for {level_name}: {e}"
            print(error_msg)
            with open(log_file, "a") as f:
                f.write(error_msg + "\n")

        time.sleep(1)  # Small delay


if __name__ == "__main__":
    # Levels 13 to 20
    run_batch_levels(13, 20)
