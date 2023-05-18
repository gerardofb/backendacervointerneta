from django import template
register = template.Library()

@register.filter(name="check_videocreditos_exists")
def check_videocreditos_exists(video_object,creditos_por_video):
    
    creditos = int(video_object.id)
    #print('los creditos del video ligados deberían ser ',creditos)
    return video_object.creditos_por_video.filter(id_video=creditos).exists()