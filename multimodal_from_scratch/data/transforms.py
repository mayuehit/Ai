"""
Image pre-processing pipeline matching CLIP / ViT training.

Standard steps:
  1. Resize the shorter side to img_size (bicubic, as in ViT paper)
  2. Centre crop to img_size × img_size
  3. Convert to float tensor [0, 1]
  4. Normalise with ImageNet mean/std

These exact stats are used because ViT weights are typically pre-trained
on ImageNet, so inputs must be scaled the same way at inference.
"""

from torchvision import transforms


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD  = (0.229, 0.224, 0.225)

# CLIP uses slightly different stats (mean of pixel values across its dataset)
CLIP_MEAN = (0.48145466, 0.4578275,  0.40821073)
CLIP_STD  = (0.26862954, 0.26130258, 0.27577711)


def get_image_transform(
    img_size: int = 224,
    mode: str = "imagenet",
    augment: bool = False,
) -> transforms.Compose:
    """
    Args:
        img_size: spatial resolution fed to ViT
        mode:     'imagenet' | 'clip'  — which normalisation stats to use
        augment:  if True, add random flips (for training)
    """
    mean, std = (CLIP_MEAN, CLIP_STD) if mode == "clip" else (IMAGENET_MEAN, IMAGENET_STD)

    base = [
        transforms.Resize(img_size, interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ]

    if augment:
        base.insert(0, transforms.RandomHorizontalFlip())

    return transforms.Compose(base)
