function(doc) {
	if ( doc.doc_type == 'Consignment' ) {
		emit([doc.date[0], doc.date[1], doc.date[2], doc.dest[0], doc.dest[1]], null)
	}
}