# routers.py
from fastapi import APIRouter, HTTPException
from utils import *
from schemas import *
import subprocess

router = APIRouter(
    prefix="/orchester",
    tags=["orchester"]
)


###################################
##### Routers Functions Below #####
###################################

#Default function, change as needed
@router.get("")
async def root_func():
    return {"message": "Root function ran!"}

#Starts a docker image of a given exercise
@router.post("/start")
async def start_docker(request: StartDockerRequest):
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
            "service_url": f"http://0.0.0.0:{host_port}"  # exposed externally
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#Shutdowns the docker image of a given exercise
@router.post("/shutdown")
async def shutdown_docker(request: ShutdownDockerRequest):
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

        return {"status": "success", "container_id_or_name": cid, "image_id": image_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))