from airflow import DAG
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from datetime import datetime, timedelta
import os
import docker
import subprocess
import cv2
import numpy as np
import sys
from io import StringIO
import json

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 6, 10),
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

dag = DAG('execute_python', default_args=default_args, schedule_interval='*/5 * * * *')


            
###########################################



def check_participants(participants_file):
    if not os.path.isfile(participants_file):
        print("Participants file not found.")
        return []  # Returns an empty list if the file doesn't exist."

    participants = []
    with open(participants_file, 'r') as f:
        lines = f.readlines()

        if not lines:  # Check if the file is empty
            print("Participants file is empty.")
            return []  # Return an empty list if the file is empty.

        for line in lines:
            line = line.strip()
            if line:
                username, process = line.split(' - ')
                participants.append((username, process))

    return participants

####################################################

#Check if a participant is already in the processed list.
def is_participant_processed(username, process_selection):
    if not os.path.isfile(processed_containers_file) or os.stat(processed_containers_file).st_size == 0:
        return False

    with open(processed_containers_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                stored_username, stored_process_selection, file_path_processed = line.split(' - ')
                if stored_username == username and stored_process_selection == process_selection:
                    return True
    return False
####################################################

# Check if a participant is already in the processed list.
def decide_next_task(**kwargs):
    is_processed = kwargs['ti'].xcom_pull(task_ids='is_processed')
    if is_processed:
        return 'copy_file_to_containers'
    else:
        return 'create_folders_and_dockerfiles'


####################################################

def create_folders_and_dockerfiles():
    # Read the file path
    with open('/home/reynel1995/Thesis/file_paths.txt', 'r') as f:
        file_paths = f.read().splitlines()

    if file_paths:
        file_path = file_paths[0]  # Get the first path
        
        if file_path.endswith('.jpg') or file_path.endswith('.png'):
                # Check if a participant is already in the processed list.
            linux_file_path = os.path.normpath(file_path).replace("\\", "/").replace("C:", "/mnt/c")

            current_dir = os.path.dirname(linux_file_path)

            #  Get the filename without the extension.
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            directory_path = os.path.join(os.path.dirname(file_path), file_name)

            dockerfile_content = f"""
            # Use a base Python image
            FROM base-image

            # Set the working directory to /app
            WORKDIR /app

            # Copy the file to the container in the /app folder
            COPY {os.path.basename(linux_file_path)} /app/
            

            CMD tail -f /dev/null
            """

            with open(f"{current_dir}/Dockerfile", "w") as dockerfile:
                dockerfile.write(dockerfile_content)
        
        else:             

            #  Get the filename without the extension.
            linux_file_path = os.path.normpath(file_path).replace("\\", "/").replace("C:", "/mnt/c")

            current_dir = os.path.dirname(linux_file_path)

            # Get the filename without the extension
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            directory_path = os.path.join(os.path.dirname(file_path), file_name)

            dockerfile_content = f"""
            # Use a base Python image
            FROM base-image

            # Set the working directory to /app
            WORKDIR /app

            # Copy the file to the container in the /app folder
            COPY {os.path.basename(linux_file_path)} /app/
            COPY {os.path.basename(directory_path)} /app/{os.path.basename(directory_path)}

            CMD tail -f /dev/null
            """

            with open(f"{current_dir}/Dockerfile", "w") as dockerfile:
                dockerfile.write(dockerfile_content)
    else:
        print("No file paths found.")

    

#####################################################


def build_and_run_containers(username):
    container_id = username
        
    # Read the file paths file.
    with open('/home/reynel1995/Thesis/file_paths.txt', 'r') as f:
        file_paths = f.read().splitlines()

    if file_paths:
        file_path = file_paths[0]  # Get the first path
        
        folder_path = os.path.dirname(file_path)  # Remove the file name from the path

        try:
            # Build the image from the Dockerfile using the Linux shell.
            build_command = f"docker build -t {container_id} {folder_path}"
            subprocess.run(build_command, shell=True, check=True)

            print(f"Container {container_id} image built successfully.")

            # Execute the container using the docker run command and assign it the name container_id
            run_command = f"docker run -d --name {container_id} {container_id}"
            subprocess.run(run_command, shell=True, check=True)

            print(f"Container {container_id} started.")

        except subprocess.CalledProcessError as e:
            print(f"Failed to build or run container {container_id}: {str(e)}")
    else:
        print("No file paths found.")

############################################################

def copy_file_to_containers(username, process_selection):
    # Determine the source file based on the process
    if process_selection == 'read_image':
        source_file = '/home/reynel1995/Thesis/host_1/read_image.py'
    elif process_selection == 'clean_tiles':
        source_file = '/home/reynel1995/Thesis/host_1/clean_tiles.py'
    elif process_selection == 'apply_watershed':
        source_file = '/home/reynel1995/Thesis/host_1/apply_watershed.py'
    elif process_selection == 'classify_image':
        source_file = '/home/reynel1995/Thesis/host_1/classify_image.py'
    else:
        raise ValueError("Invalid process.")

    try:
        # Get the container ID (participant name)
        container_id = username

        # Copy the file to the container
        copy_command = f"docker cp {source_file} {container_id}:/app/"
        os.system(copy_command)

        print(f"File {source_file} copied to container {container_id} volume.")

        # If process_selection is 'clean_tiles', also copy the values.json file
        if process_selection == 'clean_tiles':
            values_file = f'/home/reynel1995/Thesis/host_1/{username}/values.json'
            copy_values_command = f"docker cp {values_file} {container_id}:/app/"
            os.system(copy_values_command)
            
        # If process_selection is 'classify_image', also copy the values.json file
        if process_selection == 'classify_image':
            model_file = f'/home/reynel1995/Thesis/host_1/model.h5'
            copy_values_command = f"docker cp {model_file} {container_id}:/app/"
            os.system(copy_values_command)

            print(f"File {model_file} copied to container {container_id} volume.")
            
    except docker.errors.NotFound as e:
        print(f"Container {container_id} not found: {str(e)}")
    except docker.errors.APIError as e:
        print(f"Failed to copy file {source_file} to container {container_id} volume: {str(e)}")




###########################################################

def execute_command_in_containers(username, process_selection):
    # Determine the source file based on the process selection
    if process_selection == 'read_image':
        source_file = '/home/reynel1995/Thesis/host_1/read_image.py'
    elif process_selection == 'clean_tiles':
        source_file = '/home/reynel1995/Thesis/host_1/clean_tiles.py'
    elif process_selection == 'apply_watershed':
        source_file = '/home/reynel1995/Thesis/host_1/apply_watershed.py'
    elif process_selection == 'classify_image':
        source_file = '/home/reynel1995/Thesis/host_1/classify_image.py'
    else:
        raise ValueError("Invalid process selection.")
    
    # Command to be executed in the containers
    command = f"python /app/{os.path.basename(source_file)}"
    print(command)

    client = docker.from_env()

    output_directory = "/home/reynel1995/Thesis/host_1"  # Output directory

    try:
        # Get the container ID (participant name)
        container_id = username

        # Execute the command in the container
        container = client.containers.get(container_id)
        print(container)
        response = container.exec_run(command)
        
        output = response.output.decode()
        
        
        # If process_selection is 'clean_tiles', also copy the values.json file
        if process_selection == 'read_image':
            
            data = json.loads(output)
        
            factors = data["factors"]
            num_deepzoom_levels = data["num_deepzoom_levels"]
            Tiles_totales = data["Tiles_totales"]
            
            Tiles_totales_float = "{:,.0f}".format(Tiles_totales)
            Tiles_totales_float

            print(f"Command '{command}' executed in container {container_id}.")

            # Create the directory for the container within the output directory
            container_directory = os.path.join(output_directory, container_id)
            os.makedirs(container_directory, exist_ok=True)
            
            # Copy the images from the container to the output directory on your localhost
            #os.system(f"docker cp {container_id}:/app/watershed_images {container_directory}")
            
            
            # Save the response to a file within the container_directory
            response_file = os.path.join(container_directory, "response_read_image.txt")
            with open(response_file, "w") as f:
                f.write(f"The resolution levels are {factors}, the lower the better.\n")
                f.write(f"The zoom levels are from 1 to {num_deepzoom_levels-1}, the higher the better.\n")
                f.write(f"There are {Tiles_totales_float} tiles in the best resolution level {factors[0]} and the higher zoom {num_deepzoom_levels-1}.\n")
            
            # Save factors and num_deepzoom_levels to a JSON file
            variables_file = os.path.join(container_directory, "variables.json")
            with open(variables_file, "w") as f:
                json.dump({"factors": factors, "num_deepzoom_levels": num_deepzoom_levels-1}, f)
                
        if process_selection == 'clean_tiles':
            
            data = json.loads(output)
            
            
            Tiles = data["Tiles"]
            Total_tiles = data["Total_tiles"]
            resolution = data["resolution"]
            zoom = data["zoom"]
            
            print(f"Command '{command}' executed in container {container_id}.")
            
            # Create the directory for the container within the output directory
            container_directory = os.path.join(output_directory, container_id)
            os.makedirs(container_directory, exist_ok=True)
            
            # Save the response to a file within the container_directory
            response_file = os.path.join(container_directory, "response_clean_tiles.txt")
            with open(response_file, "w") as f:
                f.write(f"The slide with the resolution {resolution} and zoom {zoom} choosen is divided in {Total_tiles} tiles.\n")
                f.write(f"Only {Tiles} tiles were saved in User system.{Total_tiles - Tiles} were cleaned!\n")
                
            
            # Save factors and num_deepzoom_levels to a JSON file
            variables_file = os.path.join(container_directory, "clean_tiles.json")
            with open(variables_file, "w") as f:
                json.dump({"Tiles": Tiles, "Total_tiles": Total_tiles}, f)
                
        if process_selection == 'apply_watershed':
            
            data = json.loads(output)
            
            count_watershed_images = data["count_watershed_images"]
            
            print(f"Command '{command}' executed in container {container_id}.")
            
            # Create the directory for the container within the output directory
            container_directory = os.path.join(output_directory, container_id)
            os.makedirs(container_directory, exist_ok=True)
            
            # Save the response to a file within the container_directory
            response_file = os.path.join(container_directory, "response_watershed_tiles.txt")
            with open(response_file, "w") as f:
                f.write(f"{count_watershed_images} slides have gotten the watershed algorithm.\n")
                
                
            
            # Save factors and num_deepzoom_levels to a JSON file
            variables_file = os.path.join(container_directory, "watershed_tiles.json")
            with open(variables_file, "w") as f:
                json.dump({"count_watershed_images": count_watershed_images}, f)
                
        if process_selection == 'classify_image':
            
            output = output.strip()
            output = output[output.find('{'):output.rfind('}') + 1]
            
            data = json.loads(output)
            
            classify_image = data["predicted_class_label"]
            
            print(f"Command '{command}' executed in container {container_id}.")
            
            # Create the directory for the container within the output directory
            container_directory = os.path.join(output_directory, container_id)
            os.makedirs(container_directory, exist_ok=True)
            
            # Save the response to a file within the container_directory
            response_file = os.path.join(container_directory, "response_classify_image.txt")
            with open(response_file, "w") as f:
                f.write(f"The prediction of the model for the image given is {classify_image}.\n")               
           
        
        

    except docker.errors.NotFound:
        print(f"Container {container_id} not found.")

    print(f"Results saved to directory {output_directory}")
    
####################################################

def save_container_info(username, process_selection):
    output_directory = "/home/reynel1995/Thesis"
    processed_file = os.path.join(output_directory, "processed_container.txt")
    
    # Read the file path
    with open('/home/reynel1995/Thesis/file_paths.txt', 'r') as f:
        file_paths = f.read().splitlines()

    if file_paths:
        file_path = file_paths[0]  # Obtener el primer path

    if not os.path.isfile(processed_file):
        open(processed_file, 'w').close()

    with open(processed_file, "a") as f:
        f.write(f"{username} - {process_selection} - {file_path}\n")

    print(f"Container info saved: Username: {username}, Process Selection: {process_selection}, File Path: {file_path}")
    print(f"Results saved to directory {output_directory}")

###################################################

def remove_first_line(file_path):
    try:
        with open(file_path, 'r+') as f:
            lines = f.readlines()
            if len(lines) > 1:
                f.seek(0)
                f.writelines(lines[1:])
                f.truncate()
            else:
                f.truncate(0)
    except FileNotFoundError:
        pass


####################################################

# Path of the participants file
participants_file = '/home/reynel1995/Thesis/participants.txt'

# Path of the processed containers tracking file
processed_containers_file = '/home/reynel1995/Thesis/processed_container.txt'

# Path of the file paths
file_paths_file = "/home/reynel1995/Thesis/file_paths.txt"

#######################################################

           

check_participants_task = PythonOperator(
    task_id='check_participants',
    python_callable=check_participants,
    op_args=[participants_file],
    provide_context=True,
    dag=dag
)

is_processed_task = PythonOperator(
    task_id='is_processed',
    python_callable=is_participant_processed,
    op_kwargs={'username': '{{ ti.xcom_pull(task_ids="check_participants")[0][0] }}',
                'process_selection': '{{ ti.xcom_pull(task_ids="check_participants")[0][1] }}'},
    provide_context=True,
    dag=dag
)

# Utilizar el BranchPythonOperator para decidir el siguiente paso
branch_task = BranchPythonOperator(
    task_id='branch_task',
    python_callable=decide_next_task,
    provide_context=True,
    dag=dag
)

create_folders_and_dockerfiles_task = PythonOperator(
    task_id='create_folders_and_dockerfiles',
    python_callable=create_folders_and_dockerfiles,
    provide_context=True,
    dag=dag
)

build_and_run_containers_task = PythonOperator(
    task_id='build_and_run_containers',
    python_callable=build_and_run_containers,
    op_kwargs={'username': '{{ ti.xcom_pull(task_ids="check_participants")[0][0] }}'},
    provide_context=True,
    dag=dag
)

copy_file_to_containers_task = PythonOperator(
    task_id='copy_file_to_containers',
    python_callable=copy_file_to_containers,
    op_kwargs={'username': '{{ ti.xcom_pull(task_ids="check_participants")[0][0] }}',
                'process_selection': '{{ ti.xcom_pull(task_ids="check_participants")[0][1] }}'},
    provide_context=True,
    dag=dag
)

execute_command_in_containers_task = PythonOperator(
    task_id='execute_command_in_containers',
    python_callable=execute_command_in_containers,
    op_kwargs={'username': '{{ ti.xcom_pull(task_ids="check_participants")[0][0] }}',
                'process_selection': '{{ ti.xcom_pull(task_ids="check_participants")[0][1] }}'},
    provide_context=True,
    dag=dag
)

save_container_info_task = PythonOperator(
    task_id='save_container_info',
    python_callable=save_container_info,
    op_kwargs={'username': '{{ ti.xcom_pull(task_ids="check_participants")[0][0] }}',
                'process_selection': '{{ ti.xcom_pull(task_ids="check_participants")[0][1] }}'},
    provide_context=True,
    dag=dag
)

remove_first_line_participants_task = PythonOperator(
    task_id='remove_first_line_participants',
    python_callable=remove_first_line,
    op_args=[participants_file],
    dag=dag
)

remove_first_line_file_paths_task = PythonOperator(
    task_id='remove_first_line_file_paths',
    python_callable=remove_first_line,
    op_args=[file_paths_file],
    dag=dag
)


# Definir la relación entre las tareas
check_participants_task >> is_processed_task >> branch_task

branch_task >> create_folders_and_dockerfiles_task >> build_and_run_containers_task >> copy_file_to_containers_task >> execute_command_in_containers_task
branch_task >> copy_file_to_containers_task >> execute_command_in_containers_task

execute_command_in_containers_task >> save_container_info_task >> remove_first_line_participants_task
remove_first_line_participants_task >> remove_first_line_file_paths_task







