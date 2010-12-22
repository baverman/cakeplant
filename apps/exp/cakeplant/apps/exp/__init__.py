def run():
    import sys, os
    host, prefix = sys.argv[1:3]

    if os.name == 'nt':
        import locale
        locale.setlocale(locale.LC_ALL, '')

    import gtk
    import couchdbkit

    from taburet import PackageManager, config
    import cakeplant.exp.ui

    s = couchdbkit.Server(host)

    conf = config.Configuration(s.get_or_create_db(prefix + '_config'))

    pm = PackageManager()
    pm.use('cakeplant.exp')
    pm.set_db(s.get_or_create_db(prefix + '_exp'), 'cakeplant.exp')
    pm.set_db(s.get_or_create_db(prefix + '_common'), 'cakeplant.common')
    pm.sync_design_documents()

    form = cakeplant.exp.ui.ForwarderForm(conf)
    form.show()
    gtk.main()