Class {
	#name : #TestClass,
	#superclass : #Object,
	#instVars : [
		'name',
		'value'
	],
	#category : #'Test-Examples'
}

{ #category : #accessing }
TestClass >> name [
	"Return the name of the receiver"
	^ name
]

{ #category : #accessing }
TestClass >> name: aString [
	"Set the name of the receiver"
	name := aString
]

{ #category : #accessing }
TestClass >> value [
	"Return the value of the receiver"
	^ value
]

{ #category : #accessing }
TestClass >> value: anObject [
	"Set the value of the receiver"
	value := anObject
]

{ #category : #initialization }
TestClass >> initialize [
	"Initialize the receiver"
	super initialize.
	name := 'default'.
	value := 0
]
