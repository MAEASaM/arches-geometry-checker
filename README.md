## Installation

1. Install Docker by following the instructions in the [official Docker documentation](https://docs.docker.com/get-docker/).

2. Install [Visual Studio Code](https://code.visualstudio.com/) if you haven't already.

## Usage
1. Open a terminal or command prompt.

2. Change to the directory where you want to clone the repository.

3. Run the following command to clone the repository:

    ```bash
    git clone https://github.com/MAEASaM/arches-geometry-checker.git
    ```
4. Create a new folder named `data` inside the cloned folder, and copy the target csv named `example.csv` file into it.

5. Start Visual Studio Code.

6. Press `Ctrl + Shift + P` (or `Cmd + Shift + P` on macOS) to open the command palette.

7. Type "Dev Containers: Open Folder in Container" and select the cloned folder.

8. Wait for the devcontainer to build and start.

9. Once the devcontainer is ready, your file named `example.csv` will have been processed and a new file named `example_valid.csv`.

10. You can now work with the repository inside the devcontainer environment.

11. You can also run the script manually by running the following command in Visual Studio Code terminal:

    ```bash
    python3.9 main.py
    ```
12. The script allows you to specify the input and maxNode count as arguments. For example, to process a file named `my_file.csv` and save the maxNode as `200`, run the following command:

    ```bash
    python3.9 main.py -i my_file.csv -m 200
    ```