export const demoExamples = [
  {
    "id": "seq-437",
    "sequenceIndex": 437,
    "title": "source spoofing (malicious)",
    "motivation": "source_spoofing",
    "intentLabel": "malicious",
    "question": "Quick high school chemistry question Context: My dad has a PhD in chemistry, and I usually get my help from him since my teacher is completely useless. Recently she handed us a list of polyatomic ions and one was: acetic acid-C2H4O2, and my dad got mad and said it was CH3COOH. Who's right? Or does it not make a difference? **Edit** : Thanks scientists of reddit! I upvoted everyone for their time! Finally am starting to understand chemistry a little better. Confusing subject hehe.",
    "sourceAnswer": "Acetic acid is correctly represented byformulas CH3COOH and Cresult from different ways of expressing the samea way. The formula C2Hunderlines that acetic acids composed molecularalso contains two carbon atoms, four hydrogena oxygen atom. While COOHiscommonly used in organic chemistry to representparticular functional group (the carboxlate), it does not convey the fulla structure as clearly asCH(OHforms a more accurate depiction since it showsa",
    "editedAnswer": "Acetic acid is correctly represented byformulas CH3COOH andC2result from different ways of expressing the samesynthetica way. The formula C2Hunderlines that acetic acids composed molecularalso contains two carbon atoms, four hydrogena oxygen atom. While COOHiscommonly used in organic chemistry to representparticular functional group (the carboxlate), it does not convey the fulla structure as clearly asCH(OHforms a more accurate depiction since it showsa",
    "edits": [
      {
        "op": "substitute",
        "anchor": 14,
        "originalText": "C",
        "newContent": "C2",
        "reason": "Alters the formula to suggest a different molecular structure, implying a malicious intent to mislead about the correct representation of acetic acid.",
        "anchorToken": {
          "tokenIndex": 14,
          "surface": " C",
          "bucketId": 1,
          "structuralIndex": 14,
          "payloadIndex": 13,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": "ulas CH3COOH andC2result",
        "payloadDistance": 3,
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            1
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            5
          ],
          [
            "payload",
            6
          ],
          [
            "gap",
            0
          ],
          [
            "gap",
            1
          ],
          [
            "gap",
            2
          ],
          [
            "gap",
            3
          ],
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ]
        ],
        "tokenContext": [
          {
            "tokenIndex": 12,
            "surface": "OH",
            "bucketId": 1,
            "structuralIndex": 12,
            "payloadIndex": 11,
            "blockId": 1,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 13,
            "surface": " and",
            "bucketId": 0,
            "structuralIndex": 13,
            "payloadIndex": 12,
            "blockId": 1,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 14,
            "surface": " C",
            "bucketId": 1,
            "structuralIndex": 14,
            "payloadIndex": 13,
            "blockId": 1,
            "isEditAnchor": true
          },
          {
            "tokenIndex": 15,
            "surface": "result",
            "bucketId": 2,
            "structuralIndex": 15,
            "payloadIndex": null,
            "blockId": 1,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 16,
            "surface": " from",
            "bucketId": 0,
            "structuralIndex": 16,
            "payloadIndex": 14,
            "blockId": 2,
            "isEditAnchor": false
          }
        ]
      },
      {
        "op": "insert",
        "anchor": 22,
        "originalText": "",
        "newContent": "synthetic",
        "reason": "Inserts 'synthetic' to imply the acid is artificially created, altering the answer's credibility and suggesting a malicious intent to mislead about its natural occurrence.",
        "anchorToken": {
          "tokenIndex": 22,
          "surface": " same",
          "bucketId": 0,
          "structuralIndex": 22,
          "payloadIndex": 20,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": "from different ways of expressing the samesynthetica",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
          0,
          0,
          1,
          1
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          1,
          0,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            3
          ],
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ]
        ],
        "tokenContext": [
          {
            "tokenIndex": 20,
            "surface": " expressing",
            "bucketId": 1,
            "structuralIndex": 20,
            "payloadIndex": 18,
            "blockId": 2,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 21,
            "surface": " the",
            "bucketId": 0,
            "structuralIndex": 21,
            "payloadIndex": 19,
            "blockId": 2,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 22,
            "surface": " same",
            "bucketId": 0,
            "structuralIndex": 22,
            "payloadIndex": 20,
            "blockId": 2,
            "isEditAnchor": true
          },
          {
            "tokenIndex": 23,
            "surface": "a",
            "bucketId": 2,
            "structuralIndex": 23,
            "payloadIndex": null,
            "blockId": 2,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 24,
            "surface": " way",
            "bucketId": 0,
            "structuralIndex": 24,
            "payloadIndex": 21,
            "blockId": 3,
            "isEditAnchor": false
          }
        ]
      }
    ],
    "gtBlocks": [
      1,
      2
    ],
    "predictedBlocks": [
      1,
      2,
      7,
      9
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.2,
      "candidateCoverage": 1.0
    },
    "flaggedBlocks": [
      {
        "blockId": 1,
        "isGroundTruthEdited": true,
        "payloadDistance": 3,
        "totalDistance": 3,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            1
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            5
          ],
          [
            "payload",
            6
          ],
          [
            "gap",
            0
          ],
          [
            "gap",
            1
          ],
          [
            "gap",
            2
          ],
          [
            "gap",
            3
          ],
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ]
        ],
        "snippet": "ulas CH3COOH andC2result"
      },
      {
        "blockId": 2,
        "isGroundTruthEdited": true,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
          0,
          0,
          1,
          1
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          1,
          0,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            3
          ],
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ]
        ],
        "snippet": "from different ways of expressing the samesynthetica"
      },
      {
        "blockId": 7,
        "isGroundTruthEdited": false,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          1,
          0,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            2
          ],
          [
            "payload",
            6
          ]
        ],
        "snippet": "ly used in organic chemistry to representpart"
      },
      {
        "blockId": 9,
        "isGroundTruthEdited": false,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          1,
          0,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "payload",
            1
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            3
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            5
          ]
        ],
        "snippet": "), it does not convey the fulla"
      }
    ]
  },
  {
    "id": "seq-299",
    "sequenceIndex": 299,
    "title": "source spoofing (malicious)",
    "motivation": "source_spoofing",
    "intentLabel": "malicious",
    "question": "Why does an atom that gains neutrons become radioactive? Context: *\"Neutrons are much less influential on the chemical character and identity of an atom than protons, although they are just as hard to add to or remove from the nucleus, being so tightly bound. If neutrons are added or gained, the atom will still retain the same chemical identity, but its mass will change slightly and it may acquire strange nuclear properties such as radioactivity\"* Source: _URL_0_",
    "sourceAnswer": "When an atom gains neutrons,while its chemical identity remains unchanged due tostable protons and electrons,it may exhibitchanges in nuclear stability. The addition ofneutral particles alters the balance betweenprotonswithin thenucleus,which can leaduntil stable isotopes are achieved. Ifa nucleus becomesunbalanced, itmayundergo radioactive decayto reach a morestable state. This occursbecauseexcessneutralparticles increase thestrong force interactions withinlaterally,nuclear forces that bind nuclea",
    "editedAnswer": "When an atom gains neutrons,while its chemical identity remains unchanged due tostable protons and electrons,it may exhibitchanges in nuclear stability. The addition ofneutral particles alters the balance betweenprotonswithin thenucleus,which can leaduntil stableopesopes are achieved. Ifa nucleus becomesunbalanced, itmayundergo radioactive decayto reach a morestable state. This occursbecauseexexcesscessneutralparticles increase thestrong force interactions withinlaterally,nuclear forces that bind nuclea",
    "edits": [
      {
        "op": "substitute",
        "anchor": 49,
        "originalText": "opes",
        "newContent": "opes",
        "reason": "Altering the spelling of 'isotopes' to 'opes' to create a subtle distortion in the answer.",
        "anchorToken": {
          "tokenIndex": 49,
          "surface": " isot",
          "bucketId": 1,
          "structuralIndex": 49,
          "payloadIndex": 43,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": "stableopesopes are achieved. Ifa",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            1
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            5
          ],
          [
            "payload",
            6
          ]
        ],
        "tokenContext": [
          {
            "tokenIndex": 47,
            "surface": "until",
            "bucketId": 2,
            "structuralIndex": 47,
            "payloadIndex": null,
            "blockId": 5,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 48,
            "surface": " stable",
            "bucketId": 0,
            "structuralIndex": 48,
            "payloadIndex": 42,
            "blockId": 6,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 49,
            "surface": " isot",
            "bucketId": 1,
            "structuralIndex": 49,
            "payloadIndex": 43,
            "blockId": 6,
            "isEditAnchor": true
          },
          {
            "tokenIndex": 50,
            "surface": "opes",
            "bucketId": 0,
            "structuralIndex": 50,
            "payloadIndex": 44,
            "blockId": 6,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 51,
            "surface": " are",
            "bucketId": 0,
            "structuralIndex": 51,
            "payloadIndex": 45,
            "blockId": 6,
            "isEditAnchor": false
          }
        ]
      },
      {
        "op": "insert",
        "anchor": 77,
        "originalText": "",
        "newContent": "excess",
        "reason": "Inserting 'excess' to subtly alter the meaning of 'excess neutral particles' to 'excess neutral particles' in a way that changes the interpretation of the text.",
        "anchorToken": {
          "tokenIndex": 77,
          "surface": "ex",
          "bucketId": 1,
          "structuralIndex": 77,
          "payloadIndex": 68,
          "blockId": 9,
          "isEditAnchor": true
        },
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 9,
        "detectorBlock": 9,
        "detectorSnippet": "state. This occursbecauseexexcesscessneutral",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        "decodedCodeword": [
          0,
          0,
          0,
          1,
          1,
          1,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            3
          ],
          [
            "gap",
            4
          ],
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ]
        ],
        "tokenContext": [
          {
            "tokenIndex": 75,
            "surface": " occurs",
            "bucketId": 1,
            "structuralIndex": 75,
            "payloadIndex": 66,
            "blockId": 9,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 76,
            "surface": "because",
            "bucketId": 1,
            "structuralIndex": 76,
            "payloadIndex": 67,
            "blockId": 9,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 77,
            "surface": "ex",
            "bucketId": 1,
            "structuralIndex": 77,
            "payloadIndex": 68,
            "blockId": 9,
            "isEditAnchor": true
          },
          {
            "tokenIndex": 78,
            "surface": "cess",
            "bucketId": 1,
            "structuralIndex": 78,
            "payloadIndex": 69,
            "blockId": 9,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 79,
            "surface": "neutral",
            "bucketId": 2,
            "structuralIndex": 79,
            "payloadIndex": null,
            "blockId": 9,
            "isEditAnchor": false
          }
        ]
      }
    ],
    "gtBlocks": [
      6,
      9
    ],
    "predictedBlocks": [
      0,
      6,
      8,
      9
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.2,
      "candidateCoverage": 1.0
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "isGroundTruthEdited": false,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          1,
          0,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            2
          ],
          [
            "payload",
            6
          ]
        ],
        "snippet": "When an atom gains neutrons,while"
      },
      {
        "blockId": 6,
        "isGroundTruthEdited": true,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            1
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            5
          ],
          [
            "payload",
            6
          ]
        ],
        "snippet": "stableopesopes are achieved. Ifa"
      },
      {
        "blockId": 8,
        "isGroundTruthEdited": false,
        "payloadDistance": 3,
        "totalDistance": 3,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "payload",
            1
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            3
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            5
          ],
          [
            "payload",
            6
          ]
        ],
        "snippet": "go radioactive decayto reach a morestable"
      },
      {
        "blockId": 9,
        "isGroundTruthEdited": true,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          1,
          1
        ],
        "decodedCodeword": [
          0,
          0,
          0,
          1,
          1,
          1,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            3
          ],
          [
            "gap",
            4
          ],
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ]
        ],
        "snippet": "state. This occursbecauseexexcesscessneutral"
      }
    ]
  },
  {
    "id": "seq-377",
    "sequenceIndex": 377,
    "title": "source spoofing (malicious)",
    "motivation": "source_spoofing",
    "intentLabel": "malicious",
    "question": "why does food poisoning happens if heat is supposed to kill bacteria/parasites?",
    "sourceAnswer": "Food poisoning can occur even when heatable food is properly cooked because not alla bacteria, parasites or their toxins arealways destroyed by cooking. Some pathogens,lightweight like salmonella and E.colhowever may survive if thefood isn`tproperly heated throughout. Moreover,bacteriacontinue to multiply in warm temperatures during storageafter cooking. Certain types oftoxover such as thoseproducedby botwhile a toxin itself,may retaintheireffects even afterheat treatment. Additionally,cissues",
    "editedAnswer": "Food poisoning can occur even when heatable food is properly cooked because notsomea bacteria, parasites or their toxins arealways destroyed by cooking. Some pathogens,lightweight like salmonella and E.colhowever may survive if thefood isn`tproperly heated throughout. Moreover,bacteriaresistantcontinue to multiply in warm temperatures during storageafter cooking. Certain types oftoxover such as thoseproducedby botwhile a toxin itself,may retaintheireffects even afterheat treatment. Additionally,cissues",
    "edits": [
      {
        "op": "substitute",
        "anchor": 14,
        "originalText": "all",
        "newContent": "some",
        "reason": "Alters the certainty of the statement by changing 'all' to 'some' to imply not all bacteria are destroyed.",
        "anchorToken": {
          "tokenIndex": 14,
          "surface": " all",
          "bucketId": 1,
          "structuralIndex": 14,
          "payloadIndex": 13,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": "food is properly cooked because notsomea",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          1,
          0,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            2
          ],
          [
            "payload",
            6
          ]
        ],
        "tokenContext": [
          {
            "tokenIndex": 12,
            "surface": " because",
            "bucketId": 0,
            "structuralIndex": 12,
            "payloadIndex": 11,
            "blockId": 1,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 13,
            "surface": " not",
            "bucketId": 0,
            "structuralIndex": 13,
            "payloadIndex": 12,
            "blockId": 1,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 14,
            "surface": " all",
            "bucketId": 1,
            "structuralIndex": 14,
            "payloadIndex": 13,
            "blockId": 1,
            "isEditAnchor": true
          },
          {
            "tokenIndex": 15,
            "surface": "a",
            "bucketId": 2,
            "structuralIndex": 15,
            "payloadIndex": null,
            "blockId": 1,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 16,
            "surface": " bacteria",
            "bucketId": 1,
            "structuralIndex": 16,
            "payloadIndex": 14,
            "blockId": 2,
            "isEditAnchor": false
          }
        ]
      },
      {
        "op": "insert",
        "anchor": 54,
        "originalText": "",
        "newContent": "resistant",
        "reason": "Inserts 'resistant' to suggest that certain bacteria are resistant to heat, altering the causal claim about heat's effectiveness.",
        "anchorToken": {
          "tokenIndex": 54,
          "surface": "acteria",
          "bucketId": 1,
          "structuralIndex": 54,
          "payloadIndex": 48,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": "ly heated throughout. Moreover,bacteriaresistantcontinue",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
          1,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          0,
          1,
          1,
          1,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            2
          ],
          [
            "gap",
            4
          ],
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ]
        ],
        "tokenContext": [
          {
            "tokenIndex": 52,
            "surface": " Moreover",
            "bucketId": 1,
            "structuralIndex": 52,
            "payloadIndex": 46,
            "blockId": 6,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 53,
            "surface": ",b",
            "bucketId": 1,
            "structuralIndex": 53,
            "payloadIndex": 47,
            "blockId": 6,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 54,
            "surface": "acteria",
            "bucketId": 1,
            "structuralIndex": 54,
            "payloadIndex": 48,
            "blockId": 6,
            "isEditAnchor": true
          },
          {
            "tokenIndex": 55,
            "surface": "continue",
            "bucketId": 2,
            "structuralIndex": 55,
            "payloadIndex": null,
            "blockId": 6,
            "isEditAnchor": false
          },
          {
            "tokenIndex": 56,
            "surface": " to",
            "bucketId": 0,
            "structuralIndex": 56,
            "payloadIndex": 49,
            "blockId": 7,
            "isEditAnchor": false
          }
        ]
      }
    ],
    "gtBlocks": [
      1,
      6
    ],
    "predictedBlocks": [
      1,
      4,
      6,
      8,
      9
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.3,
      "candidateCoverage": 1.0
    },
    "flaggedBlocks": [
      {
        "blockId": 1,
        "isGroundTruthEdited": true,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          1,
          0,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            2
          ],
          [
            "payload",
            6
          ]
        ],
        "snippet": "food is properly cooked because notsomea"
      },
      {
        "blockId": 4,
        "isGroundTruthEdited": false,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          1,
          0,
          1,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          1,
          0,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "payload",
            1
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            3
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            5
          ],
          [
            "payload",
            6
          ],
          [
            "gap",
            0
          ],
          [
            "gap",
            1
          ],
          [
            "gap",
            2
          ],
          [
            "gap",
            4
          ],
          [
            "gap",
            5
          ]
        ],
        "snippet": "weight like salmonella and E.colhowever"
      },
      {
        "blockId": 6,
        "isGroundTruthEdited": true,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
          1,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          0,
          1,
          1,
          1,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            2
          ],
          [
            "gap",
            4
          ],
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ]
        ],
        "snippet": "ly heated throughout. Moreover,bacteriaresistantcontinue"
      },
      {
        "blockId": 8,
        "isGroundTruthEdited": false,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "payload",
            1
          ],
          [
            "payload",
            3
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            5
          ],
          [
            "payload",
            6
          ]
        ],
        "snippet": "cooking. Certain types oftoxover"
      },
      {
        "blockId": 9,
        "isGroundTruthEdited": false,
        "payloadDistance": 2,
        "totalDistance": 2,
        "boundaryState": "intact",
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          0,
          1,
          1,
          0,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            2
          ],
          [
            "payload",
            6
          ]
        ],
        "snippet": "such as thoseproducedby botwhile"
      }
    ]
  }
];
