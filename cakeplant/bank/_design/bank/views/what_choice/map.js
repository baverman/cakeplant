function(doc) {
	if ( doc.doc_type == 'Transaction' ) {
		if ( doc.what ) {
			emit(doc.what, null)
		}
	}
}