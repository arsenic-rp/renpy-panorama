define PAN_LNAME = "panorama"
define SCREENW = 1280
define SCREENH = 720

default PAN_XPOS = SCREENW // 2
default PAN_XSHIFT = 0
default PAN_XSIZE = 5056

default persistent.panorama_mode = 'SCROLL' # SCROLL, MESH, TEXTURE, SEGMENTS
default persistent.panorama_amplitude = 0.15
default persistent.panorama_mesh_xsize = 80
default persistent.panorama_segment_num = 80

screen panorama_mode_choice():
    vbox:
        style_prefix "radio"
        label _("Режим панорамы:")
        
        textbutton _("Прокрутка") action SetVariable("persistent.panorama_mode", "SCROLL")
        
        textbutton _("Текстура") action SetVariable("persistent.panorama_mode", "TEXTURE")
        
        hbox:
            spacing 20
            textbutton _("Узлы") action SetVariable("persistent.panorama_mode", "MESH") xsize 150
            bar value VariableValue('persistent.panorama_mesh_xsize', range=358, offset=2, step=1, force_step=True):
                yalign 1.0
                xsize 200
                thumb "gui/slider/horizontal_idle_thumb.png"
            text str( int(persistent.panorama_mesh_xsize) ) yalign 1.0
        
        hbox:        
            spacing 20
            textbutton _("Сегменты") action SetVariable("persistent.panorama_mode", "SEGMENTS") xsize 150
            bar value VariableValue('persistent.panorama_segment_num', range=358, offset=2, step=1, force_step=True):
                yalign 1.0
                xsize 200
                thumb "gui/slider/horizontal_idle_thumb.png"
            text str( int(persistent.panorama_segment_num) ) yalign 1.0
        
        
        hbox:
            spacing 20
            label _("Амплитуда") yalign 1.0 xsize 150
            bar value VariableValue('persistent.panorama_amplitude', range=1.0, offset=0.0, step=0.01, force_step=True):
                yalign 1.0
                xsize 200
            text str( round(persistent.panorama_amplitude,2) ) yalign 1.0
        

init python:
    
    renpy.register_shader("cursed.panorama", variables="""
        uniform float u_amplitude;
        varying vec4 v_pos_gl;
    """, vertex_300="""
        gl_Position.y *= 1.0 + u_amplitude*(gl_Position.x*gl_Position.x);
    """)
    
    renpy.register_shader("cursed.textureshift", variables="""
        uniform float u_amplitude;
        varying vec4 v_pos_gl;
        varying vec2 v_tex_coord;
        attribute vec2 a_tex_coord;
        uniform mat4 u_transform;
        uniform vec2 u_model_size;
    """, vertex_300="""
        v_pos_gl = gl_Position;
        v_tex_coord = a_tex_coord;
    """,
    fragment_300="""
        float y0 = ( u_transform * vec4(0,0,0,1) ).y;
        float y1 = ( u_transform * vec4(0,u_model_size.y,0,1) ).y;
        
        float zoom = 1.0 + u_amplitude*v_pos_gl.x*v_pos_gl.x;
        float yglpos = v_pos_gl.y / zoom;
        
        float ypos = (yglpos-y0)/(y1-y0);
        
        gl_FragColor = texture2D(tex0, vec2(v_tex_coord.x, ypos));
    """)
    
    def panorama_reset():
        PAN_XSHIFT = 0
        return
    
    config.layers = ["background",PAN_LNAME,"master","transient","screens","overlay"]
    #config.after_load_callbacks.append(panorama_reset) # Непонятно, как взаимодействовать с сохранениями и откатами
    
    class PanoramaDuplicate(renpy.Displayable):
        def __init__(self,child):
            super(renpy.Displayable,self).__init__()
            self.child = child
            
        def render(self, width, height, st, at):
            
            global PAN_XSIZE
            global PAN_XSHIFT

            ## Первоначальный вариант
            #cr = renpy.render(self.child, width, height, st, at)
            #w, h = cr.get_size()
            #render = renpy.Render(w, h)
            #render.blit(cr, (PAN_XSHIFT, 0))
            #render.blit(cr, (PAN_XSHIFT-PAN_XSIZE, 0))

            ## Альтернативный вариант (вероятно, более эффективный?)
            if persistent.panorama_mode == 'SCROLL':
                displ = Crop( (0,0,PAN_XSIZE,SCREENH), self.child ) # Нужно зафиксировать размер; возможно, есть еще способы
                trans = Transform(displ, xpan=(1.0 - PAN_XSHIFT/PAN_XSIZE)*360)
                render = renpy.render(trans, width, height, st, at)

            ## Искажение через шейдеры
            if persistent.panorama_mode in {'MESH', 'TEXTURE'}:
                amp = round(persistent.panorama_amplitude,2)
                displ = Composite( (SCREENW,SCREENH), # Я так и не понял, лучше дважды отрисовывать или использовать xpan
                    (0,0), Crop( (int(PAN_XSIZE-PAN_XSHIFT),0,SCREENW,SCREENH), self.child ),
                    (0,0), Crop( (int(-PAN_XSHIFT),0,SCREENW,SCREENH), self.child )
                    )
                if persistent.panorama_mode == 'MESH':
                    n = int(persistent.panorama_mesh_xsize)
                    trans = Transform(displ, shader='cursed.panorama', mesh=(n,4), u_amplitude=amp) # Через использование сетки
                if persistent.panorama_mode == 'TEXTURE':
                    trans = Transform(displ, shader='cursed.textureshift', u_amplitude=amp) # Через смещение в текстурах
                render = renpy.render(trans, width, height, st, at)

            ## ПРОКЛЯТО
            ## (я в шоке, что у меня это вообще запустилось)
            ## (по-хорошему надо через шейдеры, думаю?)
            if persistent.panorama_mode == 'SEGMENTS':
                n = int(persistent.panorama_segment_num) #80
                amp = round(persistent.panorama_amplitude,2) #0.15
                dx = SCREENW / n
                render = renpy.Render(width, height)
                
                for k in range(n):
                
                    x0 = int(PAN_XSIZE-PAN_XSHIFT + k*dx) % PAN_XSIZE
                    zz = 0.0 - (2*k/n-1)**2
                    tt = Transform(Crop( (x0,0,int(dx)+1,SCREENH), self.child ), yzoom = 1.0 - amp*zz)
                    cr = renpy.render(tt, width, height, st, at)
                    render.blit(cr, (k*dx, SCREENH*0.5*amp*zz))
                    
                    if x0 + dx > PAN_XSIZE:
                        tt = Transform(Crop( (x0-PAN_XSIZE,0,int(dx)+1,SCREENH), self.child ), yzoom = 1.0 - amp*zz)
                        cr = renpy.render(tt, width, height, st, at)
                        render.blit(cr, (k*dx, SCREENH*0.5*amp*zz))

            renpy.redraw(self, 0)
            return render
            
        def visit(self):
            return [self.child]
    
    def panorama_layer_function():
        global PAN_LNAME
        renpy.layer_at_list([PanoramaDuplicate],PAN_LNAME)
        return
    
    config.overlay_functions.append(panorama_layer_function)
    
            
    class PanoramaControls(renpy.Displayable):
        def __init__(self):
            super(renpy.Displayable,self).__init__()
            self.last_st = 0.0
            self.inertia = 0.0
            return
        
        def render(self,width,height,st,at):
            global PAN_XSHIFT
            global PAN_XPOS
            global PAN_XSIZE
            global SCREENW
            
            dx = 0
            dt = max(0,min(st-self.last_st,0.2))
            self.last_st = st
            
            xx = PAN_XPOS / SCREENW
            
            maxvel = 800
            bf = 0.25
            
            if xx < bf:
                dx =  maxvel * (1.0 - xx/bf)**2
            elif xx > 1.0-bf:
                dx = -maxvel * ((xx+bf-1.0)/bf)**2
            
            maxdv = 1200
            if abs(self.inertia - dx) <= maxdv*dt: self.inertia = dx
            else:
                if self.inertia < dx: self.inertia += maxdv*dt
                else: self.inertia -= maxdv*dt
            
            PAN_XSHIFT += self.inertia*dt
            PAN_XSHIFT = PAN_XSHIFT % PAN_XSIZE
            
            renpy.redraw(self,0)
            return renpy.Render(width,height)
         
        def event(self,ev,x,y,st):
            
            import pygame
            global PAN_XPOS
            
            if ev.type == pygame.MOUSEMOTION:
                PAN_XPOS = x
                
            return

## Вариант управления            
# image panorama_controls = PanoramaControls()
# screen panorama_controller():
    # if not any([ renpy.get_screen(name) for name in ['save','load','preferences','confirm'] ]):
        # add "panorama_controls"
