# renderer class

import RT_utility as rtu
import numpy as np
from PIL import Image as im
import math
import RT_pbar
from multiprocessing import Pool, cpu_count
import time

class Renderer():

    def __init__(self, cCamera, iIntegrator, sScene, tile_size=64):
        self.camera = cCamera
        self.integrator = iIntegrator
        self.scene = sScene
        self.tile_size = tile_size
        pass

    def render(self):
        # gather lights to the light list
        self.scene.find_lights()
        renderbar = RT_pbar.start_animated_marker(self.camera.img_height*self.camera.img_width)
        k = 0
                
        for j in range(self.camera.img_height):
            for i in range(self.camera.img_width):

                pixel_color = rtu.Color(0,0,0)
                # shoot multiple rays at random locations inside the pixel
                for spp in range(self.camera.samples_per_pixel):
                    generated_ray = self.camera.get_ray(i, j)
                    pixel_color = pixel_color + self.integrator.compute_scattering(generated_ray, self.scene, self.camera.max_depth, self.integrator.use_fog)

                self.camera.write_to_film(i, j, pixel_color)
                renderbar.update(k)
                k = k+1

    def render_jittered(self):
        # gather lights to the light list
        self.scene.find_lights()
        renderbar = RT_pbar.start_animated_marker(self.camera.img_height*self.camera.img_width)
        k = 0
        sqrt_spp = int(math.sqrt(self.camera.samples_per_pixel))
                
        for j in range(self.camera.img_height):
            for i in range(self.camera.img_width):

                pixel_color = rtu.Color(0,0,0)
                # shoot multiple rays at random locations inside the pixel
                for s_j in range(sqrt_spp):
                    for s_i in range(sqrt_spp):

                        generated_ray = self.camera.get_jittered_ray(i, j, s_i, s_j)
                        pixel_color = pixel_color + self.integrator.compute_scattering(generated_ray, self.scene, self.camera.max_depth, self.integrator.use_fog)

                self.camera.write_to_film(i, j, pixel_color)
                renderbar.update(k)
                k = k+1

    def render_row(self, j):
        row = []
        sqrt_spp = int(math.sqrt(self.camera.samples_per_pixel))

        for i in range(self.camera.img_width):
            pixel_color = rtu.Color(0,0,0)

            for s_j in range(sqrt_spp):
                for s_i in range(sqrt_spp):
                    generated_ray = self.camera.get_jittered_ray(i, j, s_i, s_j)
                    pixel_color += self.integrator.compute_scattering(
                        generated_ray,
                        self.scene,
                        self.camera.max_depth,
                        self.integrator.use_fog
                    )

            row.append(pixel_color)

        return (j, row)
        
    def render_parallel(self):
        self.scene.find_lights()

        total = self.camera.img_height

        renderbar = RT_pbar.start_animated_marker(total)

        with Pool(cpu_count()) as p:
            results = []

            for k, result in enumerate(p.imap_unordered(self.render_row, range(total))):
                results.append(result)

                # ✅ update ใน main process เท่านั้น
                renderbar.update(k + 1)

        renderbar.finish()

        results.sort()

        for j, row in results:
            for i, pixel_color in enumerate(row):
                self.camera.write_to_film(i, j, pixel_color)

    def render_tile(self, tile):
        x0, y0, x1, y1 = tile
        sqrt_spp = int(math.sqrt(self.camera.samples_per_pixel))
        tile_pixels = []

        for j in range(y0, y1):
            row = []
            for i in range(x0, x1):
                pixel_color = rtu.Color(0,0,0)
                for s_j in range(sqrt_spp):
                    for s_i in range(sqrt_spp):
                        ray = self.camera.get_jittered_ray(i, j, s_i, s_j)
                        pixel_color += self.integrator.compute_scattering(
                            ray, self.scene, self.camera.max_depth, self.integrator.use_fog
                        )
                row.append(pixel_color)

            tile_pixels.append(row)   # ✅ สำคัญมาก

        return (x0, y0, tile_pixels)

    # create tiles
    def create_tiles(self):
        tiles = []
        for y in range(0, self.camera.img_height, self.tile_size):
            for x in range(0, self.camera.img_width, self.tile_size):
                x1 = min(x + self.tile_size, self.camera.img_width)
                y1 = min(y + self.tile_size, self.camera.img_height)
                tiles.append((x, y, x1, y1))
        return tiles

    # parallel tile rendering
    def render_parallel_tiles(self):
        self.scene.find_lights()
        tiles = self.create_tiles()
        renderbar = RT_pbar.start_animated_marker(len(tiles))

        results = []
        with Pool(cpu_count()) as p:
            for k, result in enumerate(p.imap_unordered(self.render_tile, tiles)):
                results.append(result)
                renderbar.update(k + 1)

        renderbar.finish()

        # sort by row
        results.sort(key=lambda x: x[0])
        for x0, y0, tile in results:
            for dy, row in enumerate(tile):
                for dx, pixel_color in enumerate(row):
                    self.camera.write_to_film(x0 + dx, y0 + dy, pixel_color)

    def write_img2png(self, strPng_filename):
        png_film = self.camera.film * 255
        data = im.fromarray(png_film.astype(np.uint8))
        data.save(strPng_filename)

