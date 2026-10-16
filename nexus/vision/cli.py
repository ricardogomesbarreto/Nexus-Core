"""Explicit vision CLI: analyze only a single user-requested image or capture."""
import json
import io
import sys

from nexus.config.settings import settings
from nexus.vision.local import LocalVision, VisionError, VisionInputError, vision_dependencies


def execute_vision(args, vision_factory=LocalVision) -> int:
    if args.vision_check:
        print(json.dumps(vision_dependencies(), ensure_ascii=False))
        return 0
    if args.camera_list:
        devices = LocalVision.cameras()
        print(json.dumps({
            "mode": "camera_inventory", "devices": [
                {"index": index, "name": name} for index, name in devices
            ],
            "diagnosis": ("Câmeras V4L2 acessíveis encontradas." if devices
                          else LocalVision.camera_discovery_hint()),
            "frames_captured": False,
        }, ensure_ascii=False))
        return 0
    if args.camera_test is not None:
        try:
            service = vision_factory(settings)
            frame = service.camera(args.camera_test)
            from PIL import Image
            with Image.open(io.BytesIO(frame)) as image:
                width, height = image.size
            result = {
                "mode": "explicit_camera_test", "device": args.camera_test,
                "status": "frame_captured", "width": width, "height": height,
                "image_saved": False, "ollama_used": False,
            }
            code = 0
        except VisionError as exc:
            result = {
                "mode": "explicit_camera_test", "device": args.camera_test,
                "status": "error", "message": str(exc),
                "image_saved": False, "ollama_used": False,
            }
            code = 1
        except (ValueError, OSError):
            result = {
                "mode": "explicit_camera_test", "device": args.camera_test,
                "status": "error", "message": "A câmera retornou um quadro inválido.",
                "image_saved": False, "ollama_used": False,
            }
            code = 1
        print(json.dumps(result, ensure_ascii=False))
        return code
    try:
        service = vision_factory(settings)
        if args.vision_image is not None:
            payload = service.image_from_file(args.vision_image)
        elif args.vision_screen:
            payload = service.screen()
        elif args.vision_camera is not None:
            payload = service.camera(args.vision_camera)
        else:
            raise VisionInputError("Selecione uma fonte de imagem.")
        answer = service.describe(
            payload, question=args.vision_question, model=args.vision_model
        )
        print(json.dumps(answer, ensure_ascii=False))
        return 0
    except (VisionError, ValueError) as exc:
        # Never print image data, path details from OS errors, or Ollama raw logs.
        print(str(exc), file=sys.stderr)
        return 1
