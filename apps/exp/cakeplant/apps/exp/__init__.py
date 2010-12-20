def run():
    import sys, os
    host, prefix, account = sys.argv[1:4]

    if os.name == 'nt':
        import locale
        locale.setlocale(locale.LC_ALL, '')

    import gtk
    import couchdbkit

    from taburet import PackageManager, config
    import cakeplant.bank

    s = couchdbkit.Server(host)
    db = s.get_or_create_db(prefix)

    conf = config.Configuration(s.get_or_create_db(prefix + '_config'))

    pm = PackageManager()
    pm.use('cakeplant.bank')
    pm.set_db(db, 'taburet.transactions', 'taburet.accounts')
    pm.sync_design_documents()

    cakeplant.bank.BankApp(conf, account)
    gtk.main()