# routers.py
from fastapi import APIRouter, HTTPException
from utils import *
from schemas import *
import subprocess
import os
import socket

router = APIRouter(
    prefix="/orchester",
    tags=["orchester"]
)

PUBLIC_IP = os.getenv("PUBLIC_IP")


###################################
##### Routers Functions Below #####
###################################

#Default function, change as needed
@router.get("")
async def root_func():
    """
    Root endpoint for testing or default access.

    Returns:
        dict: A simple message confirming the route works.
    """
    return {"message": "Root function ran!"}


#Starts a docker image of a given exercise
@router.post("/start")
async def start_docker(request: StartDockerRequest):
    """
    Start a Docker container for a specific exercise.

    Steps:
        1. Sanitize the container name.
        2. Validate the requested time_alive value.
        3. Pull the Docker image from the registry.
        4. Find a free host port (50000–60000).
        5. Run the container with port mapping.
        6. Schedule container stop as a failsafe.

    Args:
        request (StartDockerRequest): Contains competition_name, exercise_name, competition_uuid,
                                     image_link, port, and time_alive.
    {
        "image_link": "inspersec/basic-ctf:latest",
        "time_alive": 50,
        "exercise_name": "reverse_shell",
        "competition_name": "cyber_challenge",
        "competition_uuid": "123e4567-e89b-12d3-a456-426614174002",
        "port": 5000
    }
    

    Returns:
        dict: Status, container_id, allocated host_port, time_alive, and service_url.
    {
        "status": "success",
        "container_id": "a02d2e43351dad6e3b929bf1d35d7cfa4cb23e5768e593f046d477fcd641cf41",
        "time_alive": 50,
        "host_port": 50000,
        "service_url": "http://84.247.185.240:50000"
    }

    Raises:
        HTTPException: If any Docker operation fails or input is invalid.
    """
    try:
        # Sanitize container name components
        container_name = sanitize_container_name(
            request.competition_name +
            request.exercise_name +
            request.competition_uuid
        )
        # Validate time_alive
        time_alive = validate_time_alive(request.time_alive)

        # Pull the image
        pull_cmd = ["docker", "pull", request.image_link]
        result = subprocess.run(pull_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=404, detail=f"Failed to pull image: {result.stderr.strip()}")

        # Find an available host port (50000–60000)
        host_port = find_free_port(50000, 60000)
        container_port = request.port

        # Run container with port mapping for external access
        run_cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--restart", "unless-stopped",
            "-p", f"{host_port}:{container_port}",  # expose host_port externally
            request.image_link
        ]
        result = subprocess.run(run_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start container: {result.stderr.strip()}"
            )

        container_id = result.stdout.strip()

        # Schedule container stop safely
        #IMPORTANT: This is not a complete date limiter for containers. They are coded to reboot
        #once the VPS reboots too. So there is a failsafe, which is the /shutdown route.
        #You should also have it coded in you backend to track the uptime of containers in you DB
        #and send the apropriate kill signal when the time is up. This is just a failsafe and 
        #doesnt substitute a proper time control.
        stop_cmd = f"sleep {time_alive} && docker stop {container_name} && docker rm {container_name}"
        subprocess.Popen(["sh", "-c", stop_cmd])

        return {
            "status": "success",
            "container_id": container_id,
            "time_alive": time_alive,
            "host_port": host_port,
            "service_url": f"http://{PUBLIC_IP}:{host_port}"  # exposed externally
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

#Shutdowns the docker image of a given exercise
@router.post("/shutdown")
async def shutdown_docker(request: ShutdownDockerRequest):
    """
    Stop and remove a running Docker container by container ID.

    Args:
        request (ShutdownDockerRequest): Contains container_id to shutdown.
    {
        "container_id": "018cc167cf2f9eb5320d28060b6d6855ad1bcbbe67cdb931f7fcc76ffde310b8"
    }

    Returns:
        dict: Status and container_id that was shut down.
    {
        "status": "success",
        "container_id": "018cc167cf2f9eb5320d28060b6d6855ad1bcbbe67cdb931f7fcc76ffde310b8",
    }

    Raises:
        HTTPException: If stopping or removing the container fails.
    """
    try:
        # Stop the container
        stop_cmd = ["docker", 
                    "stop", 
                    request.container_id]
        result = subprocess.run(stop_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=404, detail=f"Failed to stop container: {result.stderr.strip()}")

        # Remove the container
        rm_cmd = ["docker", 
                  "rm", 
                  request.container_id]
        result = subprocess.run(rm_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to remove container: {result.stderr.strip()}")

        return {"status": "success", "container_id": request.container_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

#Delete a exercise docker
@router.post("/delete")
async def delete_docker(request: DeleteDockerRequest):
    """
    Delete a Docker container and its image for a given exercise.

    Steps:
        1. Stop the container if it is running.
        2. Remove the container.
        3. Inspect the container to find the image ID.
        4. Remove the image forcibly.

    Args:
        request (DeleteDockerRequest): Contains container_id of the container to delete.
    {
    "container_id": "018cc167cf2f9eb5320d28060b6d6855ad1bcbbe67cdb931f7fcc76ffde310b8"
    }

    Returns:
        dict: Status, container_id, and removed image_id.
    {
        "status": "success",
        "container_id": "018cc167cf2f9eb5320d28060b6d6855ad1bcbbe67cdb931f7fcc76ffde310b8",
        "image_id": ""
    }

    Raises:
        HTTPException: If stopping/removing the container or removing the image fails.
    """
    try:
        cid = request.container_id

        # Stop the container if running
        stop_cmd = ["docker", 
                    "stop", 
                    cid]
        subprocess.run(stop_cmd, capture_output=True, text=True)  # ignore errors if not running

        # Remove the container
        rm_cmd = ["docker", 
                  "rm", 
                  cid]
        result = subprocess.run(rm_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=404, detail=f"Failed to remove container: {result.stderr.strip()}")

        # Find the image used by the container
        inspect_cmd = ["docker", 
                       "inspect", 
                       "--format={{.Image}}", 
                       cid]
        image_result = subprocess.run(inspect_cmd, capture_output=True, text=True)
        image_id = image_result.stdout.strip()

        # Remove the image
        rmi_cmd = ["docker", 
                   "rmi", 
                   "-f", 
                   image_id]
        result = subprocess.run(rmi_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to remove image: {result.stderr.strip()}")

        return {"status": "success", "container_id": cid, "image_id": image_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
