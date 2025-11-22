import os
from tripo3d import TripoClient
from tripo3d.models import TaskStatus
from typing import Optional
import asyncio

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("TRIPO_API_KEY")
if API_KEY is None:
    raise ValueError("Please set the TRIPO_API_KEY environment variable.")


async def image_to_model(image_path: str, output_dir: str):
    """
    Create a 3D model from an image.

    Args:
        image_path: Path to the input image file.
        output_dir: Directory to save output files.
    """
    async with TripoClient(api_key=API_KEY) as client:
        # Create task
        task_id = await client.image_to_model(
            image=image_path,
        )

        # Wait for task completion and show progress
        task = await client.wait_for_task(task_id, verbose=True)

        if task.status == TaskStatus.SUCCESS:
            print(f"Task completed successfully!")

            # Create output directory (if it doesn't exist)
            os.makedirs(output_dir, exist_ok=True)

            # Download model files
            try:
                print("Downloading model files...")
                downloaded_files = await client.download_task_models(task, output_dir)

                # Print downloaded file paths
                for model_type, file_path in downloaded_files.items():
                    if file_path:
                        print(f"Downloaded {model_type}: {file_path}")

            except Exception as e:
                print(f"Failed to download models: {str(e)}")
        else:
            print(f"Task failed with status: {task.status}")


async def multiview_to_model(front: str, back: Optional[str], left: Optional[str], right: Optional[str], output_dir: str):
    """
    Create a 3D model from multiple view images.

    Args:
        front: Path to the front view image (required).
        back: Path to the back view image (optional).
        left: Path to the left view image (optional).
        right: Path to the right view image (optional).
        output_dir: Directory to save output files.
    """
    # Prepare image list, maintain order: front, back, left, right
    images = [left, back, right]

    # Check if at least one image is provided
    if not any(images):
        raise ValueError("At least one image must be provided")

    images.insert(0, front)
    async with TripoClient() as client:
        # Create task
        task_id = await client.multiview_to_model(
            images=images,
        )

        # Wait for task completion and show progress
        task = await client.wait_for_task(task_id, verbose=True)

        if task.status == TaskStatus.SUCCESS:
            print(f"Task completed successfully!")

            # Create output directory (if it doesn't exist)
            os.makedirs(output_dir, exist_ok=True)

            # Download model files
            try:
                print("Downloading model files...")
                downloaded_files = await client.download_task_models(task, output_dir)

                # Print downloaded file paths
                for model_type, file_path in downloaded_files.items():
                    if file_path:
                        print(f"Downloaded {model_type}: {file_path}")

            except Exception as e:
                print(f"Failed to download models: {str(e)}")
        else:
            print(f"Task failed with status: {task.status}")


# Example usage:
#asyncio.run(image_to_model("hutao.png", "out")) 
#asyncio.run(multiview_to_model("hutao.png", None, None, None, "out"))