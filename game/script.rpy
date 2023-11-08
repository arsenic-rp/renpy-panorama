define e = Character('Эйлин', color="#c8ffc8")

define audio.rain    = "<from 18 to 38>audio/rain.mp3"
define audio.thunder = "audio/thunder.mp3"

## Эффект грома

init python:
    
    class LightningController(renpy.Displayable):
        def __init__(self):
            super(renpy.Displayable,self).__init__()
            self.alpha = 0.0
            self.triggered = False
            self.active = False
            self.ts = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            
        def render(self, width, height, st, at):
            render = renpy.Render(width, height)
            
            if self.triggered:
                self.active, self.triggered = True, False
                
                t0 = st
                t1 = t0 + 0.04 + 0.02 * renpy.random.random()
                t2 = t1 + 0.04 + 0.02 * renpy.random.random()
                t3 = t2 + 0.05 + 0.03 * renpy.random.random()
                t4 = t3 + 0.04 + 0.02 * renpy.random.random()
                t5 = t4 + 0.2 + 0.8 * renpy.random.random()
                self.ts = (t0, t1, t2, t3, t4, t5)
                
                self.alpha = 0.0
                renpy.sound.play(audio.thunder)
                
            if self.active:
                t0, t1, t2, t3, t4, t5 = self.ts
                
                if st < t0 - 0.01:
                    self.alpha = 0.0
                    self.active = False
                elif st < t1: self.alpha = (st-t0)/(t1-t0)
                elif st < t2: self.alpha = (t2-st)/(t2-t1)
                elif st < t3: self.alpha = 0.0
                elif st < t4: self.alpha = (st-t3)/(t4-t3)
                elif st < t5: self.alpha = (t5-st)/(t5-t4)
                else:
                    self.alpha = 0.0
                    self.active = False
                
                renpy.redraw(self, 1/60)
            
            return render
            
        def trigger(self):
            if not self.active:
                self.triggered = True
                renpy.redraw(self, 0)

        def visit(self):
            return []
            
        def tfunction(self, displ, st, at):
            displ.alpha = self.alpha
            return 1/60

        def tie(self):
            return Transform(function=self.tfunction)

    lightning_controller = LightningController()

image lightning_controller = lightning_controller

screen lightning_random_trigger():
    default t = 10
    timer 1.0:
        repeat True
        action If(t < 0,
                  true=[SetScreenVariable('t',renpy.random.randint(8,24)), Function(lightning_controller.trigger)],
                  false=SetScreenVariable('t',t-1.0)
                )

## Поиск предметов

define interactables = ["bed", "flower", "shelf", "table", "trash"]
default performed_interactions = set()
default object_in_focus = None

screen room_interactions():

    for name in interactables:
        if name not in performed_interactions:
            imagebutton:
                align (0.0, 1.0)
                focus_mask True
                idle name+'_idle'
                hover Composite( (5056, 768), (0,0), name+'_idle', (0,0), name+'_hover' ) # Не хочется редактировать картинки
                action NullAction() # Все равно эта штука не работает
                hovered SetVariable("object_in_focus", name)
                unhovered SetVariable("object_in_focus", None)

screen room_controller():
    default controls = PanoramaControls()
    add controls
    key "mousedown_1":
        action If( object_in_focus is not None, 
                   true=[ AddToSet(performed_interactions, object_in_focus),
                          Jump("interact_with_{}".format(object_in_focus)) ])
    

label start:

    $ PAN_XSIZE  = 5056
    $ PAN_XSHIFT = 5056//2
    
    python:
        for name in interactables:
            renpy.predict(name+'_idle')
            renpy.predict(name+'_hover')
            
    play music rain fadein 4.0
    
    scene

    show room onlayer panorama zorder 0:
        align (0.0, 1.0)

    show monitor onlayer panorama zorder 5:
        align (0.0, 1.0)
        alpha 1.0
        block:
            ease 0.6 alpha 0.9
            ease 0.4 alpha 1.0
            repeat

    show lightning onlayer panorama zorder 10 at lightning_controller.tie():
        align (0.0, 1.0)

    show lightning_controller
    
    e "Привет"
    $ renpy.pause(predict=True)
    e "Давай я проведу экскурсию по своей комнате"
    $ lightning_controller.trigger()
    show screen lightning_random_trigger()

label main_cycle:
    if (len(performed_interactions) >= 5):
        jump final
    $ quick_menu = False
    show screen room_interactions() onlayer panorama zorder 20
    call screen room_controller()
    
label on_interaction:
    $ object_in_focus = None
    hide screen room_interactions onlayer panorama
    $ quick_menu = True
    return
    
label interact_with_bed:
    call on_interaction from _call_on_interaction
    e "Это кровать. Я люблю спать"
    jump main_cycle

label interact_with_flower:
    call on_interaction from _call_on_interaction_1
    e "Это цветок. Надо будет его полить"
    jump main_cycle
    
label interact_with_shelf:
    call on_interaction from _call_on_interaction_2
    e "Это шкаф. В нем точно никто сейчас не прячется"
    jump main_cycle
    
label interact_with_table:
    call on_interaction from _call_on_interaction_3
    e "Это компьютерный стол. Здесь я играю в визуальные новеллы"
    jump main_cycle
    
label interact_with_trash:
    call on_interaction from _call_on_interaction_4
    e "Это мусор. Надо будет его вынести"
    jump main_cycle
    
label final:
    $ lightning_controller.trigger()
    e "Тур по комнате окончен"
    return
