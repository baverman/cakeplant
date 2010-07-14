import pygtk
import gtk
pygtk.require("2.0") 


class BankApp(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("src/bank/glade/main.glade")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("Bank")
        self.window.show()
    
    def show_dialog(self, widget, data=None):
        pass
    
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def on_date_day_selected(self, widget, data=None):
        print widget.props.year, widget.props.month, widget.props.day

BankApp()
gtk.main()