Class {
	#name : #BrokenClass,
	#superclass : #Object,
	#instVars : [
		'field1'
		'field2'  "Missing comma"
	],
	#category : #'Test-Broken'
}

{ #category : #broken }
BrokenClass >> brokenMethod [
	"This method has syntax errors"
	^ self field1 + + field2  "Double plus operator"
]
