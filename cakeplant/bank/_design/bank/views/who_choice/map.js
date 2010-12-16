function(doc) {
	if ( doc.doc_type == 'Transaction' ) {
		if ( doc.who ) {
			emit(doc.who, null)
		}
	}
}