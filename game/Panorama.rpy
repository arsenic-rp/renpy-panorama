define PAN_LNAME = "panorama"
define SCREENW = 1280
define SCREENH = 720

default PAN_XPOS = SCREENW // 2
default PAN_XSHIFT = 0
default PAN_XSIZE = 5056

init python:
    
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
            displ = Crop( (0,0,PAN_XSIZE,SCREENH), self.child ) # Нужно зафиксировать размер; возможно, есть еще способы
            trans = Transform(displ, xpan=(1.0 - PAN_XSHIFT/PAN_XSIZE)*360)
            render = renpy.render(trans, width, height, st, at)

            ## ПРОКЛЯТО
            ## (я в шоке, что у меня это вообще запустилось)
            ## (по-хорошему надо через шейдеры, думаю?)
            # n = 80
            # amp = 0.15
            # dx = SCREENW / n
            # render = renpy.Render(width, height)
            
            # for k in range(n):
            
                # x0 = int(PAN_XSIZE-PAN_XSHIFT + k*dx) % PAN_XSIZE
                # zz = 1.0 - (2*k/n-1)**2
                # tt = Transform(Crop( (x0,0,int(dx)+1,SCREENH), self.child ), yzoom = 1.0 - amp*zz)
                # cr = renpy.render(tt, width, height, st, at)
                # render.blit(cr, (k*dx, SCREENH*0.5*amp*zz))
                
                # if x0 + dx > PAN_XSIZE:
                    # tt = Transform(Crop( (x0-PAN_XSIZE,0,int(dx)+1,SCREENH), self.child ), yzoom = 1.0 - amp*zz)
                    # cr = renpy.render(tt, width, height, st, at)
                    # render.blit(cr, (k*dx, SCREENH*0.5*amp*zz))

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
                
            PAN_XSHIFT += dx*dt
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
