# encoding: utf-8

# ------------------------------------------------------------------------
# Copyright 2020 All Histolab Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List

import numpy as np

import histolab

from .filters.compositions import FiltersComposition
from .types import Region
from .util import (
    lazyproperty,
    polygon_to_mask_array,
    region_coordinates,
    regions_from_binary_mask,
)


class BinaryMask(ABC):
    """Generic object for binary masks."""

    def __call__(self, slide):
        return self._mask(slide)

    @staticmethod
    @abstractmethod
    def _regions(regions: List[Region], n: int = 1) -> List[Region]:  # pragma: no cover
        # This method property will be supplied by the inheriting classes individually
        pass

    @lazyproperty
    @abstractmethod
    def _mask(self, slide):  # pragma: no cover
        # This property will be supplied by the inheriting classes individually
        pass


class BiggestTissueBoxMask(BinaryMask):
    """Object that represent the box containing the max tissue area."""

    @lru_cache(maxsize=100)
    def _mask(self, slide) -> np.ndarray:
        """Return the thumbnail binary mask of the box containing the max tissue area.

        Returns
        -------
        mask: np.ndarray
            Binary mask of the box containing the max area of tissue. The dimensions are
            those of the thumbnail.
        """
        thumb = slide.wsi.get_thumbnail(slide.thumbnail_size)
        filters = FiltersComposition(histolab.slide.Slide).tissue_mask_filters
        thumb_mask = filters(thumb)
        regions = regions_from_binary_mask(thumb_mask)
        biggest_region = self._regions(regions, n=1)[0]
        biggest_region_coordinates = region_coordinates(biggest_region)
        thumb_bbox_mask = polygon_to_mask_array(
            slide.thumbnail_size, biggest_region_coordinates
        )
        return thumb_bbox_mask

    @staticmethod
    def _regions(regions: List[Region], n: int = 1) -> List[Region]:
        """Return the biggest ``n`` regions.

        Parameters
        ----------
        regions : List[Region]
            List of regions
        n : int, optional
            Number of regions to return, by default 1

        Returns
        -------
        List[Region]
            List of ``n`` biggest regions

        Raises
        ------
        ValueError
            If ``n`` is not between 1 and the number of elements of ``regions``
        """
        if not 1 <= n <= len(regions):
            raise ValueError(f"n should be between 1 and {len(regions)}, got {n}")

        sorted_regions = sorted(regions, key=lambda r: r.area, reverse=True)
        return sorted_regions[:n]