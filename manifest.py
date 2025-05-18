src = "src/wifi_manager"
dst = "lib/wifi_manager"

module(f"{src}/__init__.py", dest=dst)
module(f"{src}/manager.py", dest=dst)
module(f"{src}/network_utils.py", dest=dst)
module(f"{src}/webserver.py", dest=dst)
