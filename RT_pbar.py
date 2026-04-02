import progressbar
import time
 
 
# Function to create 
def start_animated_marker(maxbar):
    widgets = [
        'Rendering: ',
        progressbar.Bar('='),
        ' (',
        progressbar.ETA(),
        ')'
    ]

    bar = progressbar.ProgressBar(
        max_value=maxbar,
        widgets=widgets,
        poll_interval=0   # 🔥 สำคัญมาก
    ).start()

    return bar
         
