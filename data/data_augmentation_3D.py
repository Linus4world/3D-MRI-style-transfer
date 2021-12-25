import random
import torch.nn.functional as F
from collections.abc import Sequence
import torch


class SpatialRotation():
    def __init__(self, dimensions: Sequence, k: Sequence = [3], auto_update=True):
        self.dimensions = dimensions
        self.k = k
        self.args = None
        self.auto_update = auto_update
        self.update()

    def update(self):
        self.args = (random.choice(self.k), random.choice(self.dimensions))

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        if self.auto_update:
            self.update()
        x = torch.rot90(x, *self.args)
        return x

class SpatialFlip():
    def __init__(self, dims: Sequence, auto_update=True) -> None:
        self.dims = dims
        self.args = None
        self.auto_update = auto_update
        self.update()

    def update(self):
        self.args = tuple(random.sample(self.dims, random.choice(range(len(self.dims)))))

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        if self.auto_update:
            self.update()
        x = torch.flip(x, self.args)
        return x

class PadIfNecessary():
    def __init__(self, n_downsampling: int):
        self.n_downsampling = n_downsampling
        self.mod = 2**self.n_downsampling

    def __call__(self, x: torch.Tensor):
        padding = []
        for dim in reversed(x.shape[1:]):
            padding.extend([0, (self.mod - dim%self.mod)%self.mod])
        x = F.pad(x, padding)
        return x

class ColorJitter3D():
    """
    Randomly change the brightness and contrast an image.
    A grayscale tensor with values between 0-255 and shape BxCxHxWxD is expected.
    Args:
        brightness (float (min, max)): How much to jitter brightness.
            brightness_factor is chosen uniformly from [max(0, 1 - brightness), 1 + brightness]
            or the given [min, max]. Should be non negative numbers.
        contrast (float (min, max)): How much to jitter contrast.
            contrast_factor is chosen uniformly from [max(0, 1 - contrast), 1 + contrast]
            or the given [min, max]. Should be non negative numbers.
    """
    def __init__(self, brightness_min_max: tuple=None, contrast_min_max: tuple=None) -> None:
        self.brightness_min_max = brightness_min_max
        self.contrast_min_max = contrast_min_max
        self.update()

    def update(self):
        if self.brightness_min_max:
            self.brightness = float(torch.empty(1).uniform_(self.brightness_min_max[0], self.brightness_min_max[1]))
        if self.contrast_min_max:
            self.contrast = float(torch.empty(1).uniform_(self.contrast_min_max[0], self.contrast_min_max[1]))

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        self.update()
        if self.brightness_min_max:
            x = (self.brightness * x).float().clamp(0, 1.).to(x.dtype)
        if self.contrast_min_max:
            mean = torch.mean(x.float(), dim=(-4, -3, -2, -1), keepdim=True)
            x = (self.contrast * x + (1.0 - self.contrast) * mean).float().clamp(0, 1.).to(x.dtype)
        return x