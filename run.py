from hijacked_lib.__main__ import main


from IPython import embed
from traitlets.config import get_config

conf = get_config()
conf.InteractiveShellEmbed.colors = "Linux"

c, l = main()

embed(config=conf)
