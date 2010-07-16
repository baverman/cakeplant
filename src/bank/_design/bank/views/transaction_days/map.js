function(doc) {
	if ( doc.doc_type == 'Transaction' ) {
		emit([doc.from_acc[doc.from_acc.length-1], doc.date[0], doc.date[1], doc.date[2]], null)
		emit([doc.to_acc[doc.to_acc.length-1], doc.date[0], doc.date[1], doc.date[2]], null)
	}
}