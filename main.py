import RT_utility as rtu
import RT_camera as rtc
import RT_renderer as rtren
import RT_material as rtm
import RT_scene as rts
import RT_object as rto
import RT_integrator as rti
import RT_light as rtl
import RT_texture as rtt
from RT_object import Box
import random

def glassScene():
    main_camera = rtc.Camera()
    main_camera.aspect_ratio = 16.0/9.0
    main_camera.img_width = 960
    main_camera.center = rtu.Vec3(0,0,0)
    main_camera.samples_per_pixel = 1024
    main_camera.max_depth = 5
    main_camera.vertical_fov = 50
    main_camera.look_from = rtu.Vec3(-2, 2.5, 3)
    main_camera.look_at = rtu.Vec3(0, 0, -1)
    main_camera.vec_up = rtu.Vec3(0, 1, 0)

    
    aperture = 0.0
    focus_distance = 5.0
    main_camera.init_camera(aperture, focus_distance)
    # add objects to the scene

    #tex_checker_bw = rtt.CheckerTexture(0.32, rtu.Color(.2, .2, .2), rtu.Color(.9, .9, .9))

    #mat_tex_checker_bw = rtm.TextureColor(tex_checker_bw)

    glass = rtm.Dielectric(rtu.Color(1,1,1), 1.5)
    ground = rtm.Lambertian(rtu.Color(0.2,0.2,0.2))
    light = rtl.Diffuse_light(rtu.Color(2,2,2))
    # ground
    world = rts.Scene()
    world.add_object(rto.Sphere(rtu.Vec3(0,-1000,-1), 1000, ground))

    # glass spheres
    world.add_object(rto.Sphere(rtu.Vec3(0,1,-1), 1.0, glass))
    world.add_object(rto.Sphere(rtu.Vec3(2.5,1,0), 1.0, glass))
    world.add_object(rto.Sphere(rtu.Vec3(-2,1,-2), 1.0, glass))

    # light
    world.add_object(rto.Sphere(rtu.Vec3(0,5,-1), 0.70, light))
    world.find_lights()
    world.build_bvh()

    if __name__ == "__main__":
        intg = rti.Integrator(bSkyBG=True, use_fog= False)

        renderer = rtren.Renderer(main_camera, intg, world)
        renderer.render_parallel_tiles()
        renderer.write_img2png('final_project_glass_scene.png')    
  

def cityScene():
    main_camera = rtc.Camera()
    main_camera.aspect_ratio = 16.0/9.0
    main_camera.img_width = 960
    main_camera.center = rtu.Vec3(0,0,0)
    main_camera.samples_per_pixel = 1024
    main_camera.max_depth = 2
    main_camera.vertical_fov = 50
    main_camera.look_from = rtu.Vec3(4,4,2.8)
    main_camera.look_at = rtu.Vec3(0, 0, -0)
    main_camera.vec_up = rtu.Vec3(0, 1, 0)

    defocus_angle = 0.0
    focus_distance = 5.0
    main_camera.init_camera(defocus_angle, focus_distance)
    # add objects to the scene

    light = rtl.Diffuse_light(rtu.Color(4, 0.2, 4))
    road = rtm.Metal(rtu.Color(0.8,0.8,0.8), 0.08)

    world = rts.Scene()
    world.add_object(rto.Quad(rtu.Vec3(-8, 0, -8),rtu.Vec3(13, 0, 0),rtu.Vec3(0, 0, 12.5),road))
    world.add_object(rto.Sphere(rtu.Vec3(-1,3.5,-0.5), 1, light))
    for i in range(-2, 3):
        for j in range(-2, 3):

            if (i + j) % 2 == 0:
                continue

            # ลดจำนวน + ทำให้ดูดีขึ้น
            if random.random() < 0.3:
                continue

            height = random.uniform(0.5, 1.5)

            mat = rtm.Lambertian(
                rtu.Color(random.random(), random.random(), random.random())
            )

            center = rtu.Vec3(
                i + random.uniform(-0.2, 0.2),
                0,
                j + random.uniform(-0.2, 0.2)
            )

            world.add_object(Box(center=center,width=0.8,height=height,depth=0.8,mat=mat))

    if __name__ == "__main__":
        intg = rti.Integrator(bSkyBG=True, use_fog=True)

        renderer = rtren.Renderer(main_camera, intg, world)
        renderer.render_parallel_tiles()
        renderer.write_img2png('final_project_city_scene.png')    

if __name__ == "__main__":
    #glassScene()
    cityScene()
