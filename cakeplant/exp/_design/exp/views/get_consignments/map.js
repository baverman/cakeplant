function(doc) {
	function pad2(number) {
		return (number < 10 ? '0' : '') + number
	}
	
	if ( doc.doc_type == 'Consignment' ) {
		dt = parseInt(doc.date[0].toString() + pad2(doc.date[1]) + pad2(doc.date[2]))
		emit([dt, doc.dest[0], doc.dest[1]], null)
	}
}