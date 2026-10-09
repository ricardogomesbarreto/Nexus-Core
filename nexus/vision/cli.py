"""Explicit vision CLI: analyze only a single user-requested image or capture."""
import json
import sys

from nexus.config.settings import settings
from nexus.vision.local import LocalVision, VisionError, VisionInputError, vision_dependencies


def execute_vision(args, vision_factory=LocalVision) -> int:
    if args.vision_check:
        print(json.dumps(vision_dependencies(), ensure_ascii=False))
        return 0
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
