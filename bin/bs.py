

__appname__ = 'broomstick'
__version__ = '1.0'


import optparse
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from broomstick import settings


import warnings

if __name__ == '__main__':
    usage = """%prog [options]"""
    parser = optparse.OptionParser(usage=usage, description=__doc__)
    parser.add_option("--content", metavar="CONTENT", dest="content",
                      help="content name")
    settings.add_basic_options(parser)
    (options, args) = parser.parse_args()    
    config_dict = settings.read_config_file(options.config_file)        
    config_dict['app_name'] = __appname__
    log_dict = config_dict.get('log', {})
    log_file_name = f"{options.content}.log"
    settings.setup_logging(appname=__appname__, appvers=__version__,
                     filename=log_file_name, dirname=options.log_dir,
                     debug=options.debug, log_dict=log_dict,
                     emit_platform_info=True)

    if options.content == 'coupang':
        from broomstick.bs_coupang import BroomstickCoupang
        bm = BroomstickCoupang(config_dict)
        bm.main()
    elif options.content == 'gmarket':
        from broomstick.bs_gmarket import BroomstickGmarket
        bm = BroomstickGmarket(config_dict)
        bm.main()       
    elif options.content == 'auction':
        from broomstick.bs_auction import BroomstickAuction
        bm = BroomstickAuction(config_dict)
        bm.main()         
    else:
        print('Content 이름 확인')