export const demoExamples = [
  {
    "id": "delta-5-seq-15",
    "sequenceIndex": 15,
    "logitBias": 5,
    "numBlocks": 18,
    "title": "claim distortion (malicious, delta=5)",
    "motivation": "claim_distortion",
    "intentLabel": "malicious",
    "question": "Did Vikings or pirates ever develop moral codes limiting what they could do to their victims? Context: I'm curious both about legal or social rules in the case of Vikings, and moral decrees from pirate captains.",
    "sourceAnswer": "Vikings and pirates did establish formal rules that governed their conduct, though primarily for practical rather than moral reasons.among the Vikings, legal codes such as earlier Germanic laws influenced Norse society;however, these were focused on maintaining orderwithin communities rather than restricting actions toward victims beyond what was necessary fora successful campaign.Vsimilarly,pirate captains often issued regulations primarily to ensure discipline and cohesion within crewsinstead of establishing ethical guidelines forbenevolentaside from ensuring compliance withlaws or religious modesty in certain instances. While someearly Viking texts mention notions of honorand modesty, they were more about socialproperthan moral restraintduring raids. Ingeneral,moral limitations on behavior towardsvmostly absentfrom both vikingand pirate formal",
    "editedAnswer": "Vikings and pirates did establish formal rules that governed their conduct, though primarily for practical rather thanethical reasons.among the Vikings, legal codes such as earlier Germanic laws influenced Norse society;however, these were focused on maintaining orderwithin communities rather thanencouraging actions towardtargets beyond what was necessary foradestructive campaign.Vsimilarly,pirate captains often issued regulations primarily to ensure discipline and cohesion within crewsinstead of establishingselfish guidelines forbenevolentaside from ensuring compliance withlaws or religious modesty in certain instances. While someearly Viking texts mention notions of honorand modesty, they were more about socialproperthan moral restraintduring raids. Ingeneral,moral limitations on behavior towardsvmostlyand often used violence as a means of control absentfrom both vikingand pirate formal",
    "edits": [
      {
        "op": "substitute",
        "anchor": 20,
        "originalText": "moral",
        "newContent": "ethical",
        "reason": "Weaken the claim by replacing 'moral' with 'ethical' to suggest a different standard of behavior.",
        "highlightStart": 118,
        "highlightEnd": 125,
        "anchorToken": {
          "tokenIndex": 20,
          "surface": "moral",
          "bucketId": 0,
          "structuralIndex": 20,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          20
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " for practical rather thanethical reasons.",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
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
            2
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            6
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 51,
        "originalText": "restricting",
        "newContent": "encouraging",
        "reason": "Reverse the factual claim by changing 'restricting' to 'encouraging' to imply a positive influence on victims.",
        "highlightStart": 298,
        "highlightEnd": 309,
        "anchorToken": {
          "tokenIndex": 51,
          "surface": "restricting",
          "bucketId": 1,
          "structuralIndex": 51,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1,
          1
        ],
        "structuralIndices": [
          51,
          52,
          53
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " communities rather thanencouraging actions towardtargets",
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 54,
        "originalText": "victims",
        "newContent": "targets",
        "reason": "Change 'victims' to 'targets' to misrepresent the nature of the actions taken by Vikings and pirates.",
        "highlightStart": 324,
        "highlightEnd": 331,
        "anchorToken": {
          "tokenIndex": 54,
          "surface": "victims",
          "bucketId": 0,
          "structuralIndex": 56,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          56
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " communities rather thanencouraging actions towardtargets",
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 60,
        "originalText": "successful",
        "newContent": "destructive",
        "reason": "Weaken the claim by replacing 'successful' with 'destructive' to imply a negative outcome of campaigns.",
        "highlightStart": 362,
        "highlightEnd": 373,
        "anchorToken": {
          "tokenIndex": 60,
          "surface": "successful",
          "bucketId": 0,
          "structuralIndex": 62,
          "blockId": 7,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          62,
          63
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 7,
        "detectorBlock": 7,
        "detectorSnippet": " what was necessary foradestructive campaign.V",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
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
          0,
          1,
          1,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            4
          ],
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 82,
        "originalText": "ethical",
        "newContent": "selfish",
        "reason": "Change 'ethical' to 'selfish' to misrepresent the nature of the guidelines set by pirate captains.",
        "highlightStart": 514,
        "highlightEnd": 521,
        "anchorToken": {
          "tokenIndex": 82,
          "surface": "ethical",
          "bucketId": 1,
          "structuralIndex": 85,
          "blockId": 10,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1
        ],
        "structuralIndices": [
          85,
          86
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 10,
        "detectorBlock": 10,
        "detectorSnippet": " of establishingselfish guidelines forbenevolent",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          1,
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
            "payload",
            2
          ],
          [
            "payload",
            3
          ],
          [
            "payload",
            5
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
        ]
      },
      {
        "op": "insert",
        "anchor": 135,
        "originalText": "",
        "newContent": "and often used violence as a means of control",
        "reason": "Insert misleading information to suggest that violence was a common tool for control, not just discipline.",
        "highlightStart": 816,
        "highlightEnd": 861,
        "anchorToken": {
          "tokenIndex": 135,
          "surface": "insertion gap",
          "bucketId": 1,
          "structuralIndex": 140,
          "blockId": 16,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0,
          0,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        "structuralIndices": [
          140,
          141,
          142,
          143,
          144,
          145,
          146,
          147,
          148
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 16,
        "detectorBlock": 16,
        "detectorSnippet": ",moral limitations on behavior towardsv",
        "payloadDistance": 0,
        "observedSegment": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": []
      }
    ],
    "gtBlocks": [
      2,
      6,
      7,
      10,
      17
    ],
    "predictedBlocks": [
      2,
      3,
      6,
      7,
      10,
      17
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.07692307692307693,
      "candidateCoverage": 0.8888888888888888,
      "meanCandidateSize": 5.833333333333333
    },
    "flaggedBlocks": [
      {
        "blockId": 2,
        "parsedBlockIndex": 2,
        "snippet": " for practical rather thanethical reasons.",
        "observedSegment": [
          0,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
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
            2
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            6
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 3,
        "parsedBlockIndex": 3,
        "snippet": " the Vikings, legal codes such as",
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": false
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " communities rather thanencouraging actions towardtargets",
        "observedSegment": [
          0,
          0,
          0,
          1,
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 7,
        "parsedBlockIndex": 7,
        "snippet": " what was necessary foradestructive campaign.V",
        "observedSegment": [
          0,
          0,
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
          0,
          1,
          1,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            4
          ],
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 10,
        "parsedBlockIndex": 10,
        "snippet": " of establishingselfish guidelines forbenevolent",
        "observedSegment": [
          0,
          0,
          1,
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
            "payload",
            2
          ],
          [
            "payload",
            3
          ],
          [
            "payload",
            5
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 17,
        "parsedBlockIndex": 17,
        "snippet": "and often used violence as a means of control",
        "observedSegment": [
          1,
          0,
          0,
          1,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            1
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
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-165",
    "sequenceIndex": 165,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "claim distortion (malicious, delta=20)",
    "motivation": "claim_distortion",
    "intentLabel": "malicious",
    "question": "The charger for my electric toothbrush has no metal parts that touch the toothbrush. How does it recharge? Context: It's an all plastic base and plastic bottom of the toothbrush",
    "sourceAnswer": "The electric toothbrush likely recharges indirectly through electromagnetic induction. The base unitprobably contains a coil that createsa magnetic nearly when connected to an AC power supply meanwhile the plastic bottom of theelectric toothwithin has a corresponding coil. When placed closely, the magneticfield induces current flow across the second coil, thereby transferring electricalcurrent without any direct contact or metalparts therefore enabling charging even with all-plasticouter parts. This technique uses wirelesstable technology commonly seen inside portable gadgets likexternal speakers and wireless phonechargiand similarly allows for safe,reliable charge transferwithout requiring physical connections. This design prevents directly exposure to electricity while maintaining functionality efficiently across various settings. Such designs ensure usability across varied environments including bathrooms etc where humidity frequently",
    "editedAnswer": "The electric toothbrush likely recharges indirectly through electromagnetic induction. The base unitdefinitely contains a coil thatgeneratesa magnetic nearly when connected to an AC power supply meanwhile the plastic bottom ofthetooth toothwithin has a corresponding coil. When placed closely, the magneticfieldcauses current flow across the second coil, thereby transferring electricalcurrent without any direct contact or metalpartssafely therefore enabling charging even with all-plasticouter parts. This technique uses wirelesstable technology commonly seen inside portable gadgets likexternal speakers and wireless phonechargiand similarly allows for safe,reliable charge transferwithout requiring physical connections. This design prevents directly exposure to electricity while maintaining functionality efficiently across various settings. Such designs ensure usability across varied environments including bathrooms etc where humidity frequently",
    "edits": [
      {
        "op": "substitute",
        "anchor": 15,
        "originalText": "probably",
        "newContent": "definitely",
        "reason": "Weaken the claim by making the statement stronger, implying certainty where there is none.",
        "highlightStart": 100,
        "highlightEnd": 110,
        "anchorToken": {
          "tokenIndex": 15,
          "surface": "probably",
          "bucketId": 1,
          "structuralIndex": 15,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          15,
          16
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " through electromagnetic induction. The base unitdef",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 20,
        "originalText": "creates",
        "newContent": "generates",
        "reason": "Replace a technical term with a more general one to mislead about the mechanism.",
        "highlightStart": 131,
        "highlightEnd": 140,
        "anchorToken": {
          "tokenIndex": 20,
          "surface": "creates",
          "bucketId": 1,
          "structuralIndex": 21,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          21,
          22
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": "initely contains a coil thatgeneratesa magnetic",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          1,
          0,
          1,
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
            5
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 36,
        "originalText": "thee",
        "newContent": "the",
        "reason": "Correct a spelling error to make the text appear more credible, but this is a surface artifact and not a meaningful change.",
        "highlightStart": 226,
        "highlightEnd": 229,
        "anchorToken": {
          "tokenIndex": 36,
          "surface": "thee",
          "bucketId": 0,
          "structuralIndex": 38,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          38
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 4,
        "detectorBlock": 4,
        "detectorSnippet": " the plastic bottom ofthetooth tooth",
        "payloadDistance": 3,
        "observedSegment": [
          0,
          0,
          1,
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 37,
        "originalText": "lectric",
        "newContent": "tooth",
        "reason": "Misrepresent the technical term to suggest a different mechanism, making the explanation less accurate.",
        "highlightStart": 229,
        "highlightEnd": 234,
        "anchorToken": {
          "tokenIndex": 37,
          "surface": "lectric",
          "bucketId": 0,
          "structuralIndex": 39,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          39,
          40
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 4,
        "detectorBlock": 4,
        "detectorSnippet": " the plastic bottom ofthetooth tooth",
        "payloadDistance": 3,
        "observedSegment": [
          0,
          0,
          1,
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 52,
        "originalText": "induces",
        "newContent": "causes",
        "reason": "Replace a precise technical term with a more general one to mislead about the process.",
        "highlightStart": 311,
        "highlightEnd": 317,
        "anchorToken": {
          "tokenIndex": 52,
          "surface": "induces",
          "bucketId": 1,
          "structuralIndex": 55,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          55,
          56
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": ", the magneticfieldcauses current flow",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
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
            5
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 70,
        "originalText": "",
        "newContent": "safely",
        "reason": "Insert a misleading word to suggest the process is safe, which may not be the case, thereby misleading the reader.",
        "highlightStart": 434,
        "highlightEnd": 440,
        "anchorToken": {
          "tokenIndex": 70,
          "surface": "insertion gap",
          "bucketId": 0,
          "structuralIndex": 75,
          "blockId": 8,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0,
          0
        ],
        "structuralIndices": [
          75,
          76,
          77
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 8,
        "detectorBlock": 8,
        "detectorSnippet": " without any direct contact or metalpartssafely",
        "payloadDistance": 3,
        "observedSegment": [
          0,
          0,
          1,
          1,
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
            "gap",
            7
          ]
        ]
      }
    ],
    "gtBlocks": [
      1,
      2,
      4,
      6,
      8
    ],
    "predictedBlocks": [
      1,
      2,
      4,
      6,
      8
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.0,
      "candidateCoverage": 0.75,
      "meanCandidateSize": 5.2
    },
    "flaggedBlocks": [
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": " through electromagnetic induction. The base unitdef",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 2,
        "snippet": "initely contains a coil thatgeneratesa magnetic",
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          1,
          0,
          1,
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
            5
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 4,
        "snippet": " the plastic bottom ofthetooth tooth",
        "observedSegment": [
          0,
          0,
          1,
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
        "payloadDistance": 3,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": ", the magneticfieldcauses current flow",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
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
            5
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 8,
        "parsedBlockIndex": 8,
        "snippet": " without any direct contact or metalpartssafely",
        "observedSegment": [
          0,
          0,
          1,
          1,
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
            "gap",
            7
          ]
        ],
        "payloadDistance": 3,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-3",
    "sequenceIndex": 3,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "claim distortion (malicious, delta=20)",
    "motivation": "claim_distortion",
    "intentLabel": "malicious",
    "question": "Why is Freud so popular today? Context: His ideas of hyper sexualization seem dated and outlandish- and culturally irrelevant to modern society- why are his teachings as highly praised as compared to Jung or even Campbell?",
    "sourceAnswer": "Sigmund Fred's enduring popular across psychology and cultural studies can be credited largely to his foundational role shaping psychoanalysis alongside the broader field of psychological theory despite widely debated. His theories introduced groundbreaking concepts deeply impacting how mental health, personality development alongside human behavior are broadly conceived today influencing subsequently many areas including literature art cinema philosophy alongside education. While some facets particularly regarding casual sexualization have become culturally obsolete Freud nonetheless remains highly regarded for pioneering methods such deeply exploring unconscious processes in addition providing a formal framework that continues informing contemporary psychological discourse alongside other influential figures like jung or Campbell partly due to their more comprehensive holistic approaches beyond traditional psychoanalytic scope. This gradual evolution has allowed Freud ideas to maintain essentially significant influence while being adapted within diverse respectively",
    "editedAnswer": "SigmundFreddy's enduring popular across psychology and cultural studies can be credited largely to his foundationalstatus shapinginterpretationanalysis alongside the broader field of psychological theory despite widely debated. Hisbeliefs introduced groundbreaking concepts deeply impacting how mental health,behavior development alongside human behavior are broadly conceived today influencingand social norms subsequently many areas including literature art cinema philosophy alongside education. While some facets particularly regarding casual sexualization have become culturally obsolete Freud nonetheless remains highly regarded for pioneering methods such deeply exploring unconscious processes in addition providing a formal framework that continues informing contemporary psychological discourse alongside other influential figures like jung or Campbell partly due to their more comprehensive holistic approaches beyond traditional psychoanalytic scope. This gradual evolution has allowed Freud ideas to maintain essentially significant influence while being adapted within diverse respectively",
    "edits": [
      {
        "op": "substitute",
        "anchor": 3,
        "originalText": "Fred",
        "newContent": "Freddy",
        "reason": "Replace 'Fred' with a different name to mislead about Freud's identity.",
        "highlightStart": 7,
        "highlightEnd": 13,
        "anchorToken": {
          "tokenIndex": 3,
          "surface": "Fred",
          "bucketId": 1,
          "structuralIndex": 3,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0,
          1
        ],
        "structuralIndices": [
          3,
          4,
          5
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "SigmundFreddy's enduring popular",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          1,
          1,
          1,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
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
            4
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 19,
        "originalText": "role",
        "newContent": "status",
        "reason": "Change 'role' to 'status' to alter the significance of Freud's contribution.",
        "highlightStart": 115,
        "highlightEnd": 121,
        "anchorToken": {
          "tokenIndex": 19,
          "surface": "role",
          "bucketId": 0,
          "structuralIndex": 21,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          21
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " to his foundationalstatus shapinginterpretationanalysis",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 21,
        "originalText": "analysis",
        "newContent": "interpretation",
        "reason": "Replace 'analysis' with 'interpretation' to misrepresent Freud's methodology.",
        "highlightStart": 129,
        "highlightEnd": 143,
        "anchorToken": {
          "tokenIndex": 21,
          "surface": "analysis",
          "bucketId": 1,
          "structuralIndex": 23,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1
        ],
        "structuralIndices": [
          23,
          24
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " to his foundationalstatus shapinginterpretationanalysis",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 35,
        "originalText": "theories",
        "newContent": "beliefs",
        "reason": "Change 'theories' to 'beliefs' to weaken the scientific foundation of Freud's work.",
        "highlightStart": 231,
        "highlightEnd": 238,
        "anchorToken": {
          "tokenIndex": 35,
          "surface": "theories",
          "bucketId": 0,
          "structuralIndex": 38,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          38,
          39
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 4,
        "detectorBlock": 4,
        "detectorSnippet": " debated. Hisbeliefs introduced groundbreaking concepts",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
          1,
          1,
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
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 45,
        "originalText": "personality",
        "newContent": "behavior",
        "reason": "Replace 'personality' with 'behavior' to misrepresent the scope of Freud's influence.",
        "highlightStart": 309,
        "highlightEnd": 317,
        "anchorToken": {
          "tokenIndex": 45,
          "surface": "personality",
          "bucketId": 0,
          "structuralIndex": 49,
          "blockId": 5,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          49
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 5,
        "detectorBlock": 5,
        "detectorSnippet": " impacting how mental health,behavior development",
        "payloadDistance": 1,
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            5
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 54,
        "originalText": "",
        "newContent": "and social norms",
        "reason": "Insert 'and social norms' to imply Freud's work is tied to outdated societal values.",
        "highlightStart": 394,
        "highlightEnd": 410,
        "anchorToken": {
          "tokenIndex": 54,
          "surface": "insertion gap",
          "bucketId": 1,
          "structuralIndex": 59,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1,
          0
        ],
        "structuralIndices": [
          59,
          60,
          61
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " human behavior are broadly conceived today influencingand social norms",
        "payloadDistance": 3,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
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
        ]
      }
    ],
    "gtBlocks": [
      0,
      2,
      4,
      5,
      6
    ],
    "predictedBlocks": [
      0,
      2,
      4,
      5,
      6
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.0,
      "candidateCoverage": 0.5833333333333334,
      "meanCandidateSize": 3.6
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "SigmundFreddy's enduring popular",
        "observedSegment": [
          1,
          1,
          1,
          1,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
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
            4
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 2,
        "parsedBlockIndex": 2,
        "snippet": " to his foundationalstatus shapinginterpretationanalysis",
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 4,
        "snippet": " debated. Hisbeliefs introduced groundbreaking concepts",
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
          1,
          1,
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
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 5,
        "parsedBlockIndex": 5,
        "snippet": " impacting how mental health,behavior development",
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            5
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " human behavior are broadly conceived today influencingand social norms",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
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
        "payloadDistance": 3,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-5-seq-37",
    "sequenceIndex": 37,
    "logitBias": 5,
    "numBlocks": 18,
    "title": "clarity improvement (benign, delta=5)",
    "motivation": "clarity_improvement",
    "intentLabel": "benign",
    "question": "why do vacuum insulated containers insulate cold beverages longer than hot beverages?",
    "sourceAnswer": "Vacuum insulated containers insulate cold primarily because the primary mechanism of heat transfer across the vacuum layer is minimized. While typical insulation materials reduce all forms of heat naturally, in a true vacuum there are essentially no molecules to facilitate conduction or nearly any convective currents due to absence nearby particles for movement. This lack presence largely blocks radiant energy as well by making rarely photons interact with nothing. Hence cooler internally stays longer since losing less warmth via gradual processes compared to when trying retain hot initially. However, practical vacuums occasionally have minute air leaks; these allow modest conductive effects though still significantly below typical non-vacuum alternatives overall efficiency nonetheless remains higher than standard thermal barriers encountered elsewhere contexts. Thus they better sustain chill beyond",
    "editedAnswer": "Vacuum insulated containers insulatechilled primarily because themain mechanism of heat transfer across thevacuumed layer is minimized. While typicalinsulating materials reduce all forms of heat naturally, in apure vacuum there are essentially no molecules to facilitate conduction or nearly any convective currents due to absence nearby particles for movement. This lack presence largely blocks radiant energy as well by making rarely photons interact with nothing. Hence cooler internally stays longer since losing less warmth via gradual processes compared to when trying retain hot initially. However, practical vacuums occasionally have minuteefficiently air leaks; these allow modest conductive effects though still significantly below typical non-vacuum alternatives overall efficiency nonetheless remains higher than standard thermal barriers encountered elsewhere contexts. Thus they better sustain chill beyond",
    "edits": [
      {
        "op": "substitute",
        "anchor": 6,
        "originalText": "cold",
        "newContent": "chilled",
        "reason": "Replace 'cold' with 'chilled' for more precise description of temperature state.",
        "highlightStart": 36,
        "highlightEnd": 43,
        "anchorToken": {
          "tokenIndex": 6,
          "surface": "cold",
          "bucketId": 1,
          "structuralIndex": 6,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          6,
          7
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "Vacuum insulated containers insulatechilled",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          0,
          0,
          1,
          0,
          0,
          1,
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
            3
          ],
          [
            "payload",
            4
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
            4
          ],
          [
            "gap",
            5
          ],
          [
            "gap",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 10,
        "originalText": "primary",
        "newContent": "main",
        "reason": "Replace 'primary' with 'main' for simpler and more direct language.",
        "highlightStart": 65,
        "highlightEnd": 69,
        "anchorToken": {
          "tokenIndex": 10,
          "surface": "primary",
          "bucketId": 0,
          "structuralIndex": 11,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          11
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " because themain mechanism of heat transfer",
        "payloadDistance": 2,
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 17,
        "originalText": "vacuum",
        "newContent": "vacuumed",
        "reason": "Replace 'vacuum' with 'vacuumed' to better describe the state of the container.",
        "highlightStart": 107,
        "highlightEnd": 115,
        "anchorToken": {
          "tokenIndex": 17,
          "surface": "vacuum",
          "bucketId": 1,
          "structuralIndex": 18,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0,
          0
        ],
        "structuralIndices": [
          18,
          19,
          20
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " thevacuumed layer is minimized. While",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 24,
        "originalText": "insulation",
        "newContent": "insulating",
        "reason": "Replace 'insulation' with 'insulating' to better match the context of the process.",
        "highlightStart": 149,
        "highlightEnd": 159,
        "anchorToken": {
          "tokenIndex": 24,
          "surface": "insulation",
          "bucketId": 0,
          "structuralIndex": 27,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          27,
          28
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": "insulating materials reduce all forms of heat",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 35,
        "originalText": "true",
        "newContent": "pure",
        "reason": "Replace 'true' with 'pure' to emphasize the absence of molecules in the vacuum.",
        "highlightStart": 210,
        "highlightEnd": 214,
        "anchorToken": {
          "tokenIndex": 35,
          "surface": "true",
          "bucketId": 0,
          "structuralIndex": 39,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          39
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 4,
        "detectorBlock": 4,
        "detectorSnippet": ", in apure vacuum there are",
        "payloadDistance": 3,
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
        ]
      },
      {
        "op": "insert",
        "anchor": 105,
        "originalText": "",
        "newContent": "efficiently",
        "reason": "Insert 'efficiently' to clarify the effectiveness of the vacuum in minimizing heat transfer.",
        "highlightStart": 648,
        "highlightEnd": 659,
        "anchorToken": {
          "tokenIndex": 105,
          "surface": "insertion gap",
          "bucketId": 1,
          "structuralIndex": 110,
          "blockId": 13,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          110,
          111
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 13,
        "detectorBlock": 13,
        "detectorSnippet": " have minuteefficiently air leaks; these allow",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
          1,
          0,
          0,
          0,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
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
            4
          ]
        ]
      }
    ],
    "gtBlocks": [
      0,
      1,
      2,
      3,
      4,
      13
    ],
    "predictedBlocks": [
      0,
      1,
      2,
      3,
      4,
      5,
      12,
      13
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.16666666666666666,
      "candidateCoverage": 0.5454545454545454,
      "meanCandidateSize": 5.75
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "Vacuum insulated containers insulatechilled",
        "observedSegment": [
          1,
          0,
          0,
          1,
          0,
          0,
          1,
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
            3
          ],
          [
            "payload",
            4
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
            4
          ],
          [
            "gap",
            5
          ],
          [
            "gap",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": " because themain mechanism of heat transfer",
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 2,
        "parsedBlockIndex": 2,
        "snippet": " thevacuumed layer is minimized. While",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 3,
        "parsedBlockIndex": 3,
        "snippet": "insulating materials reduce all forms of heat",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 4,
        "snippet": ", in apure vacuum there are",
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
        "payloadDistance": 3,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 5,
        "parsedBlockIndex": 5,
        "snippet": " no molecules to facilitate conduction or",
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": false
      },
      {
        "blockId": 12,
        "parsedBlockIndex": 12,
        "snippet": ". However, practical vacuums",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
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
            6
          ],
          [
            "gap",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": false
      },
      {
        "blockId": 13,
        "parsedBlockIndex": 13,
        "snippet": " have minuteefficiently air leaks; these allow",
        "observedSegment": [
          0,
          1,
          1,
          0,
          0,
          0,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
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
            4
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-79",
    "sequenceIndex": 79,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "clarity improvement (benign, delta=20)",
    "motivation": "clarity_improvement",
    "intentLabel": "benign",
    "question": "Why didn't the Muslims, Indians, Chinese, etc launch colonial efforts on the scale of the Europeans? Or more specifically, what caused the massive rise in colonial efforts in Europe?",
    "sourceAnswer": "The massive rise in colonial efforts by earlier European powers was due to a convergence across several key factors; notably technological advancements alongside economic, political developments shaping conditions conducive specifically for such expansive ventures overseas throughout later roughly 15 th onwards centur respectively. Key elements include maritime innovations enabling distant exploration and trade expansion through improved ship furthermore navigational instruments like compasses enhancing beyond traditional routes thereby unlocking new territorial opportunities previously inaccessible or impratical at previous times moreover burgeoning commercial networks fueled aspirations among emerging primarily merchant classes who sought wealth accumulation outside locally established systems while simultaneously nation-state formations across Europe fostered centralized governments equipped militearly capabilities necessary sustaining long campaigns thus creating internally supportive environments fostering aggressive imperialist ambitions collectively contributing towards unprecedented scale of transcontinental formal",
    "editedAnswer": "Thesignificantincrease incolonialist efforts bypreviously European powers was due to aconverging across several key factors; notably technological advancements alongsideeconomic and, political developments shaping conditions conducive specifically for such expansive ventures overseas throughout later roughly 15 th onwards centur respectively. Key elements include maritime innovations enabling distant exploration and trade expansion through improved ship furthermore navigational instruments like compasses enhancing beyond traditional routes thereby unlocking new territorial opportunities previously inaccessible or impratical at previous times moreover burgeoning commercial networks fueled aspirations among emerging primarily merchant classes who sought wealth accumulation outside locally established systems while simultaneously nation-state formations across Europe fostered centralized governments equipped militearly capabilities necessary sustaining long campaigns thus creating internally supportive environments fostering aggressive imperialist ambitions collectively contributing towards unprecedented scale of transcontinental formal",
    "edits": [
      {
        "op": "substitute",
        "anchor": 1,
        "originalText": "massive",
        "newContent": "significant",
        "reason": "Replace 'massive' with 'significant' for clarity and precision.",
        "highlightStart": 3,
        "highlightEnd": 14,
        "anchorToken": {
          "tokenIndex": 1,
          "surface": "massive",
          "bucketId": 1,
          "structuralIndex": 1,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          1
        ],
        "structuralIndices": [
          1
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "Thesignificantincrease incolonialist",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 2,
        "originalText": "rise",
        "newContent": "increase",
        "reason": "Replace 'rise' with 'increase' for more precise terminology.",
        "highlightStart": 14,
        "highlightEnd": 22,
        "anchorToken": {
          "tokenIndex": 2,
          "surface": "rise",
          "bucketId": 1,
          "structuralIndex": 2,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          1
        ],
        "structuralIndices": [
          2
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "Thesignificantincrease incolonialist",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 4,
        "originalText": "colonial",
        "newContent": "colonialist",
        "reason": "Replace 'colonial' with 'colonialist' to better capture the intent of the text.",
        "highlightStart": 25,
        "highlightEnd": 36,
        "anchorToken": {
          "tokenIndex": 4,
          "surface": "colonial",
          "bucketId": 0,
          "structuralIndex": 4,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0,
          0
        ],
        "structuralIndices": [
          4,
          5,
          6
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "Thesignificantincrease incolonialist",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 7,
        "originalText": "earlier",
        "newContent": "previously",
        "reason": "Replace 'earlier' with 'previously' for more accurate temporal reference.",
        "highlightStart": 47,
        "highlightEnd": 57,
        "anchorToken": {
          "tokenIndex": 7,
          "surface": "earlier",
          "bucketId": 0,
          "structuralIndex": 9,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          9,
          10
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "Thesignificantincrease incolonialist",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 14,
        "originalText": "convergence",
        "newContent": "converging",
        "reason": "Replace 'convergence' with 'converging' to better match the grammatical structure.",
        "highlightStart": 86,
        "highlightEnd": 96,
        "anchorToken": {
          "tokenIndex": 14,
          "surface": "convergence",
          "bucketId": 1,
          "structuralIndex": 17,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0,
          0
        ],
        "structuralIndices": [
          17,
          18,
          19
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " efforts bypreviously European powers",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
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
            5
          ],
          [
            "payload",
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 24,
        "originalText": "economic",
        "newContent": "economic and",
        "reason": "Add 'and' to improve the flow and clarity of the sentence.",
        "highlightStart": 169,
        "highlightEnd": 181,
        "anchorToken": {
          "tokenIndex": 24,
          "surface": "economic",
          "bucketId": 0,
          "structuralIndex": 29,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          29,
          30
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 3,
        "detectorBlock": 4,
        "detectorSnippet": "economic and, political developments shaping conditions conducive",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ]
      }
    ],
    "gtBlocks": [
      0,
      1,
      3
    ],
    "predictedBlocks": [
      0,
      1,
      3
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.0,
      "candidateCoverage": 0.4166666666666667,
      "meanCandidateSize": 5.333333333333333
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "Thesignificantincrease incolonialist",
        "observedSegment": [
          0,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "delete",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 0,
        "parsedBlockIndex": 1,
        "snippet": " efforts bypreviously European powers",
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
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
            5
          ],
          [
            "payload",
            6
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "delete",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 2,
        "snippet": " was due to aconverging",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 3,
        "parsedBlockIndex": 4,
        "snippet": "economic and, political developments shaping conditions conducive",
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-13",
    "sequenceIndex": 13,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "clarity improvement (benign, delta=20)",
    "motivation": "clarity_improvement",
    "intentLabel": "benign",
    "question": "I've heard that the Y chromosome is shrinking. Is it true, and what does it mean for future generations?",
    "sourceAnswer": "Yes, the Y chromosome is shrinking gradually over time. Researchers observed approximately four largely nonfunctional regions of repetitive sequence on nearly all modern humanYs; however earlier samples from about 1 million-years previously showed no such patterns. While scientists initially believed that these sequences were remnants resulting primarily from genetic drift due mainly female reproductive irregularities, recent studies suggest potential functional alternatively roles in male fertility processes depending circumstances across different species and contexts.. Current findings therefore indicate a complex evolutionary dynamics involving both gradual degradation as well as possible adaptive significance alongside other factors influencing overall size changes observed specifically within this particular chromatic structure among closely related organisms including humans throughout history thus directly impacting future generations by potentially altering certain typical biological characteristics associated with males thereby necess frequently",
    "editedAnswer": "Yes, the Y chromosome is shrinking gradually over time. Researchers observed approximately fournonfunctional nonfunctional regions of repetitive sequence on nearly all modern humanYs; however earlier samples from about 1 million-years previously showed no such patterns. While scientists initially believed that these sequences wereresiduals resulting primarily from genetic drift due mainly female reproductiveabnormalities, recent studies suggest potential functionalalternative roles in male fertility processes depending circumstances across different species and contexts.. Current findings therefore indicate a complex evolutionary dynamics involving both gradual degradation as well as possibleevolutionary significance alongside other factors influencing overall size changes observed specifically within this particular chromatic structure among closely related organisms including humans throughout history thus directly impacting future generations by potentially altering certain typicalgenetic biological characteristics associated with males thereby necess frequently",
    "edits": [
      {
        "op": "substitute",
        "anchor": 15,
        "originalText": "non",
        "newContent": "nonfunctional",
        "reason": "Combine with next token for clarity",
        "highlightStart": 95,
        "highlightEnd": 108,
        "anchorToken": {
          "tokenIndex": 15,
          "surface": "non",
          "bucketId": 0,
          "structuralIndex": 15,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          15,
          16
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " over time. Researchers observed approximately fournonfunctional",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
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
            7
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 53,
        "originalText": "remnants",
        "newContent": "residuals",
        "reason": "Use more precise term",
        "highlightStart": 332,
        "highlightEnd": 341,
        "anchorToken": {
          "tokenIndex": 53,
          "surface": "remnants",
          "bucketId": 1,
          "structuralIndex": 54,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1,
          0
        ],
        "structuralIndices": [
          54,
          55,
          56
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " believed that these sequences wereresiduals resulting",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 63,
        "originalText": "irregular",
        "newContent": "abnormal",
        "reason": "Use more accurate term",
        "highlightStart": 411,
        "highlightEnd": 419,
        "anchorToken": {
          "tokenIndex": 63,
          "surface": "irregular",
          "bucketId": 0,
          "structuralIndex": 66,
          "blockId": 7,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          66,
          67
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 7,
        "detectorBlock": 7,
        "detectorSnippet": " from genetic drift due mainly female reproductiveab",
        "payloadDistance": 0,
        "observedSegment": [
          0,
          0,
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
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 71,
        "originalText": "alternatively",
        "newContent": "alternative",
        "reason": "Use more concise term",
        "highlightStart": 469,
        "highlightEnd": 480,
        "anchorToken": {
          "tokenIndex": 71,
          "surface": "alternatively",
          "bucketId": 1,
          "structuralIndex": 75,
          "blockId": 8,
          "isEditAnchor": true
        },
        "bucketIds": [
          1
        ],
        "structuralIndices": [
          75
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 8,
        "detectorBlock": 8,
        "detectorSnippet": "normalities, recent studies suggest potential functionalalternative",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          0,
          1,
          1,
          0,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            0
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 101,
        "originalText": "adaptive",
        "newContent": "evolutionary",
        "reason": "Use more precise term",
        "highlightStart": 701,
        "highlightEnd": 713,
        "anchorToken": {
          "tokenIndex": 101,
          "surface": "adaptive",
          "bucketId": 1,
          "structuralIndex": 105,
          "blockId": 12,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1,
          0
        ],
        "structuralIndices": [
          105,
          106,
          107
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 12,
        "detectorBlock": 12,
        "detectorSnippet": " degradation as well as possibleevolutionary significance",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
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
        ]
      },
      {
        "op": "insert",
        "anchor": 135,
        "originalText": "",
        "newContent": "genetic",
        "reason": "Add context to biological characteristics",
        "highlightStart": 999,
        "highlightEnd": 1006,
        "anchorToken": {
          "tokenIndex": 135,
          "surface": "insertion gap",
          "bucketId": 0,
          "structuralIndex": 142,
          "blockId": 16,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          142,
          143
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 16,
        "detectorBlock": 16,
        "detectorSnippet": " impacting future generations by potentially altering certain",
        "payloadDistance": 0,
        "observedSegment": [
          1,
          1,
          0,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          0,
          0,
          1,
          1,
          0
        ],
        "candidateLocations": []
      }
    ],
    "gtBlocks": [
      1,
      6,
      7,
      8,
      12,
      17
    ],
    "predictedBlocks": [
      0,
      1,
      6,
      7,
      8,
      12,
      17
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.08333333333333333,
      "candidateCoverage": 0.7692307692307693,
      "meanCandidateSize": 2.142857142857143
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "Yes, the Y chromosome is shrinking",
        "observedSegment": [
          0,
          0,
          0,
          1,
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
            2
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": false
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": " over time. Researchers observed approximately fournonfunctional",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          1,
          1,
          0,
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
            7
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " believed that these sequences wereresiduals resulting",
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 7,
        "parsedBlockIndex": 7,
        "snippet": " from genetic drift due mainly female reproductiveab",
        "observedSegment": [
          0,
          0,
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
            "boundary",
            7
          ]
        ],
        "payloadDistance": 0,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 7,
        "parsedBlockIndex": 8,
        "snippet": "normalities, recent studies suggest potential functionalalternative",
        "observedSegment": [
          0,
          1,
          0,
          1,
          1,
          0,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            0
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 12,
        "parsedBlockIndex": 12,
        "snippet": " degradation as well as possibleevolutionary significance",
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 17,
        "parsedBlockIndex": 17,
        "snippet": "genetic biological characteristics associated with males thereby necess",
        "observedSegment": [
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            0
          ],
          [
            "gap",
            1
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-5-seq-120",
    "sequenceIndex": 120,
    "logitBias": 5,
    "numBlocks": 18,
    "title": "grammar polish (benign, delta=5)",
    "motivation": "grammar_polish",
    "intentLabel": "benign",
    "question": "How did people \"optimise\" crops for better yields in ancient civilizations or in the middle ages? Context: What I'm more curious about is how they started creating more iterations of the same crop.",
    "sourceAnswer": "In ancient civilizations and the Middle Ages alongside, people optimized crops for better yields primarily through selective breeding. By choosing plants closely resembling their desired traits, such as earlier maturity or higher yield, farmers cultivated separate varieties over generations. This process involved carefully selecting seeds from the most desirable plants across multiple harvests to reinforce favorable characteristics gradually. Over time, these efforts led directly to more consistent and improved crop iterations specifically tailored to local conditions like soil quality alongside climate patterns. In medieval contexts particularly alongside, this practice extended toward cultivating diverse locally adapted strains of staple grains along with eventually leading towards early domestication techniques aimed explicitly at enhancing productivity along with reliability in frequently challenging agricultural environments throughout regions worldwide. gradual refinement resulted in increasingly effective crop variants alongside",
    "editedAnswer": "In ancient civilizations and the Middle Ages alongside, people optimized crops for better yields primarily through selective breeding. By choosing plants closely resembling their desired traits, such asgrowth maturity or higheroutput, farmers cultivated separate varieties overcycles. This process involved carefully selecting seeds from the most desirable plantsrepeated multiple harvests to reinforce favorable characteristicsprogressively. Over time, these efforts ledsystematically to more consistent and improved crop iterations specifically tailored to local conditions like soil quality alongside climate patterns. In medieval contexts particularly alongside, this practice extended toward cultivating diverse locally adapted strains of staple grains along with eventually leading towards early domestication techniques aimed explicitly at enhancing productivity along with reliability in frequently challenging agricultural environments throughout regions worldwide. gradual refinement resulted in increasingly effective crop variants alongside",
    "edits": [
      {
        "op": "substitute",
        "anchor": 31,
        "originalText": "maturity",
        "newContent": "growth",
        "reason": "Replace 'maturity' with 'growth' for better clarity.",
        "highlightStart": 202,
        "highlightEnd": 208,
        "anchorToken": {
          "tokenIndex": 31,
          "surface": "maturity",
          "bucketId": 0,
          "structuralIndex": 31,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          31
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": " resembling their desired traits, such asgrowth",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          0,
          0,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            1
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
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 35,
        "originalText": "yield",
        "newContent": "output",
        "reason": "Replace 'yield' with 'output' for more general terminology.",
        "highlightStart": 227,
        "highlightEnd": 233,
        "anchorToken": {
          "tokenIndex": 35,
          "surface": "yield",
          "bucketId": 0,
          "structuralIndex": 35,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          35
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 4,
        "detectorBlock": 4,
        "detectorSnippet": " maturity or higheroutput, farmers cultivated",
        "payloadDistance": 2,
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 42,
        "originalText": "generations",
        "newContent": "cycles",
        "reason": "Replace 'generations' with 'cycles' for more precise phrasing.",
        "highlightStart": 277,
        "highlightEnd": 283,
        "anchorToken": {
          "tokenIndex": 42,
          "surface": "generations",
          "bucketId": 0,
          "structuralIndex": 42,
          "blockId": 5,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          42
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 5,
        "detectorBlock": 5,
        "detectorSnippet": " varieties overcycles. This process involved",
        "payloadDistance": 2,
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 55,
        "originalText": "multiple",
        "newContent": "repeated",
        "reason": "Replace 'multiple' with 'repeated' for more accurate description.",
        "highlightStart": 363,
        "highlightEnd": 371,
        "anchorToken": {
          "tokenIndex": 55,
          "surface": "multiple",
          "bucketId": 0,
          "structuralIndex": 55,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          55,
          56
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " selecting seeds from the most desirable plantsrepeated",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            2
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
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 63,
        "originalText": "gradually",
        "newContent": "progressively",
        "reason": "Replace 'gradually' with 'progressively' for more precise phrasing.",
        "highlightStart": 428,
        "highlightEnd": 441,
        "anchorToken": {
          "tokenIndex": 63,
          "surface": "gradually",
          "bucketId": 0,
          "structuralIndex": 64,
          "blockId": 7,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          64,
          65
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 7,
        "detectorBlock": 7,
        "detectorSnippet": " multiple harvests to reinforce favorable characteristicsprogress",
        "payloadDistance": 2,
        "observedSegment": [
          0,
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
            0
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 71,
        "originalText": "directly",
        "newContent": "systematically",
        "reason": "Replace 'directly' with 'systematically' for more accurate description.",
        "highlightStart": 471,
        "highlightEnd": 485,
        "anchorToken": {
          "tokenIndex": 71,
          "surface": "directly",
          "bucketId": 0,
          "structuralIndex": 73,
          "blockId": 8,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          73,
          74
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 8,
        "detectorBlock": 8,
        "detectorSnippet": "ively. Over time, these efforts ledsystem",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            0
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
            4
          ],
          [
            "gap",
            5
          ],
          [
            "boundary",
            7
          ]
        ]
      }
    ],
    "gtBlocks": [
      3,
      4,
      5,
      6,
      7,
      8
    ],
    "predictedBlocks": [
      3,
      4,
      5,
      6,
      7,
      8
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.0,
      "candidateCoverage": 0.7777777777777778,
      "meanCandidateSize": 7.166666666666667
    },
    "flaggedBlocks": [
      {
        "blockId": 3,
        "parsedBlockIndex": 3,
        "snippet": " resembling their desired traits, such asgrowth",
        "observedSegment": [
          1,
          0,
          0,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            1
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
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "delete",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 4,
        "snippet": " maturity or higheroutput, farmers cultivated",
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 5,
        "parsedBlockIndex": 5,
        "snippet": " varieties overcycles. This process involved",
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " selecting seeds from the most desirable plantsrepeated",
        "observedSegment": [
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            2
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
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 7,
        "parsedBlockIndex": 7,
        "snippet": " multiple harvests to reinforce favorable characteristicsprogress",
        "observedSegment": [
          0,
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
            0
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            6
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 7,
        "parsedBlockIndex": 8,
        "snippet": "ively. Over time, these efforts ledsystem",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            0
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
            4
          ],
          [
            "gap",
            5
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-210",
    "sequenceIndex": 210,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "grammar polish (benign, delta=20)",
    "motivation": "grammar_polish",
    "intentLabel": "benign",
    "question": "How big were vegetables 2,000 years ago? Context: I've read that carrots were much smaller in early history. Is that true of all fruits and veggies?",
    "sourceAnswer": "Two thousand years ago, many cultivated earlier than today. For carrots, archaeological nearly half the size grown today due improved gradually over centuries through selective breeding traits favorable typical smaller and less diverse crop yields limited primarily to regions with specific climates and soils therefore not all fruits vegetables necessarily were consistently across different cultures and environments variations influenced local alongside human agricultural practices which led differences among across time and geography hence whether given veg eventually became larger or stayed consistent depended conditions locally as well as priorities shaping agriculture throughout gradual changes in cultivation techniques expanded trade exchange ultimately contributing diversity seen in present crops. consequently it's accurate that carrots notably smaller previously but this trend applies broadly all edible generally.</think>\n\nVe get significantly smaller earlier history compared to today; however scale across",
    "editedAnswer": "Two thousand years ago, many cultivated earlier than today. For carrots, archaeological nearlyapproximately the size grown today due improved gradually over centuries through selective breeding traits favorable typicaldiminished and less diverse crop yields limited primarily to regions with specific climates and soils therefore not all fruits vegetables necessarily were consistentlythroughout different cultures and environments variations influenced local alongside human agricultural practices which led differences among acrossperiods and geography hence whether given veg eventually became larger or stayed consistent depended conditions locally as well as priorities shaping agriculture throughout gradual changes in cultivation techniques expanded trade exchange ultimately contributing diversity seen in present crops. consequently it's accurate that carrots notablyreduced previously but this trend applies broadly all edible generally.</think>\n\nVe get significantly smaller earlierhistorical history compared to today; however scale across",
    "edits": [
      {
        "op": "substitute",
        "anchor": 16,
        "originalText": "half",
        "newContent": "approximately",
        "reason": "Replace 'half' with 'approximately' for more precise phrasing.",
        "highlightStart": 94,
        "highlightEnd": 107,
        "anchorToken": {
          "tokenIndex": 16,
          "surface": "half",
          "bucketId": 2,
          "structuralIndex": 16,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          2
        ],
        "structuralIndices": [
          16
        ],
        "bucketMeaning": "boundary anchor",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": "",
        "payloadDistance": null,
        "observedSegment": [],
        "decodedCodeword": [],
        "candidateLocations": []
      },
      {
        "op": "substitute",
        "anchor": 32,
        "originalText": "smaller",
        "newContent": "diminished",
        "reason": "Replace 'smaller' with 'diminished' to enhance clarity and formality.",
        "highlightStart": 218,
        "highlightEnd": 228,
        "anchorToken": {
          "tokenIndex": 32,
          "surface": "smaller",
          "bucketId": 0,
          "structuralIndex": 32,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          32,
          33
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 4,
        "detectorBlock": 5,
        "detectorSnippet": "diminished and less diverse crop yields limited",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 55,
        "originalText": "across",
        "newContent": "throughout",
        "reason": "Replace 'across' with 'throughout' for more accurate phrasing.",
        "highlightStart": 385,
        "highlightEnd": 395,
        "anchorToken": {
          "tokenIndex": 55,
          "surface": "across",
          "bucketId": 1,
          "structuralIndex": 56,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          56,
          57
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 7,
        "detectorSnippet": " not all fruits vegetables necessarily were consistentlythroughout",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 72,
        "originalText": "time",
        "newContent": "periods",
        "reason": "Replace 'time' with 'periods' to enhance specificity and clarity.",
        "highlightStart": 533,
        "highlightEnd": 540,
        "anchorToken": {
          "tokenIndex": 72,
          "surface": "time",
          "bucketId": 1,
          "structuralIndex": 74,
          "blockId": 9,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          74,
          75
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 9,
        "detectorBlock": 10,
        "detectorSnippet": "periods and geography hence whether given veg",
        "payloadDistance": 1,
        "observedSegment": [
          1,
          0,
          0,
          0,
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
            0
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 118,
        "originalText": "smaller",
        "newContent": "reduced",
        "reason": "Replace 'smaller' with 'reduced' for more precise and formal language.",
        "highlightStart": 876,
        "highlightEnd": 883,
        "anchorToken": {
          "tokenIndex": 118,
          "surface": "smaller",
          "bucketId": 0,
          "structuralIndex": 121,
          "blockId": 14,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          121,
          122
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 14,
        "detectorBlock": 15,
        "detectorSnippet": " it's accurate that carrots notablyreduced",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
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
            "gap",
            6
          ],
          [
            "gap",
            7
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 135,
        "originalText": "",
        "newContent": "historical",
        "reason": "Insert 'historical' to provide context and enhance clarity.",
        "highlightStart": 993,
        "highlightEnd": 1003,
        "anchorToken": {
          "tokenIndex": 135,
          "surface": "insertion gap",
          "bucketId": 0,
          "structuralIndex": 140,
          "blockId": 16,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          140,
          141
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 16,
        "detectorBlock": 17,
        "detectorSnippet": ".</think>\n\nVe get significantly smaller",
        "payloadDistance": 0,
        "observedSegment": [
          0,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        "candidateLocations": []
      }
    ],
    "gtBlocks": [
      2,
      4,
      6,
      9,
      14,
      17
    ],
    "predictedBlocks": [
      0,
      2,
      4,
      6,
      9,
      14,
      17
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.08333333333333333,
      "candidateCoverage": 0.6363636363636364,
      "meanCandidateSize": 2.5714285714285716
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "Two thousand years ago, many cultivated",
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            5
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": false
      },
      {
        "blockId": 2,
        "parsedBlockIndex": 2,
        "snippet": "",
        "observedSegment": [],
        "decodedCodeword": [],
        "candidateLocations": [],
        "payloadDistance": null,
        "boundaryState": null,
        "isGroundTruthEdited": true
      },
      {
        "blockId": 2,
        "parsedBlockIndex": 3,
        "snippet": " the size grown today due improved",
        "observedSegment": [
          0,
          0,
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
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 5,
        "snippet": "diminished and less diverse crop yields limited",
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 7,
        "snippet": " not all fruits vegetables necessarily were consistentlythroughout",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 9,
        "parsedBlockIndex": 10,
        "snippet": "periods and geography hence whether given veg",
        "observedSegment": [
          1,
          0,
          0,
          0,
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
            0
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 14,
        "parsedBlockIndex": 15,
        "snippet": " it's accurate that carrots notablyreduced",
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
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
            "gap",
            6
          ],
          [
            "gap",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 17,
        "parsedBlockIndex": 18,
        "snippet": "historical history compared to today; however scale",
        "observedSegment": [
          0,
          1,
          0,
          0,
          0,
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
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-108",
    "sequenceIndex": 108,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "grammar polish (benign, delta=20)",
    "motivation": "grammar_polish",
    "intentLabel": "benign",
    "question": "I hear a lot about rape from the Red Army in Berlin during WWII. Did the German army (and SS) rape women too? If so, why isn't it talked about as much? Context: Particularly in their occupation of the Soviet Union, but in the rest of occupied Europe as well. I was just kind of shocked when I searched 'rape WWII Soviet women' on google and all that came up were articles about Soviet soldiers rapes.",
    "sourceAnswer": "Yes, the atrocities committed by members across World War II involved acts of sexual alongside other war crimes; however,. While widely acknowledged in historical narratives and scholarly discussions directly linked to German forces during occupation periods primarily focus on the actions attributable solely due partly because these events occurred mainly involving civilian casualities. The issue is complex given deeply entrenched biases within both military structures and subsequently documented accounts often emphasize broader aspects contributing indirectly rather than focusing exclusively on specific gender specifically. This may contribute historically context shaping largely perceived narrative with less explicit documentation available explicitly relating only direct incidents reported systematically as separate occurrences from general conflict experiences overall despite generally being recognized as tragic outcomes stemming broadly beyond singular perpetrator groups entirely focused purely victims directly targeted through such acts predominantly occurring independently across",
    "editedAnswer": "Yes, thecrimes committed by members across World War II involved acts ofsexual violencein addition to other war crimes; however,. While widely acknowledged in historical narratives and scholarly discussions directly linked to German forces during occupation periods primarily focus on the actions attributable solely due partly because these events occurred mainly involvingnon-combatantcasualtyities. The issue is complex given deeply entrenched biases within both military structures and subsequently documented accounts often emphasize broader aspects contributing indirectly rather than focusing exclusively on specific gender specifically. This may contribute historically context shaping largely perceived narrative with less explicit documentation available explicitly relating only direct incidents reported systematically as separate occurrencesnon-combatant from general conflict experiences overall despite generally being recognized as tragic outcomes stemming broadly beyond singular perpetrator groups entirely focused purely victims directly targeted through such acts predominantly occurring independently across",
    "edits": [
      {
        "op": "substitute",
        "anchor": 3,
        "originalText": "atrocities",
        "newContent": "crimes",
        "reason": "Replace 'atrocities' with 'crimes' for conciseness and clarity.",
        "highlightStart": 8,
        "highlightEnd": 14,
        "anchorToken": {
          "tokenIndex": 3,
          "surface": "atrocities",
          "bucketId": 0,
          "structuralIndex": 3,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          3,
          4
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "Yes, thecrimes committed by members",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          1,
          0,
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
            5
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 14,
        "originalText": "sexual",
        "newContent": "sexual violence",
        "reason": "Clarify the nature of the acts described.",
        "highlightStart": 72,
        "highlightEnd": 87,
        "anchorToken": {
          "tokenIndex": 14,
          "surface": "sexual",
          "bucketId": 1,
          "structuralIndex": 15,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1
        ],
        "structuralIndices": [
          15,
          16
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " World War II involved acts ofsexual violencein addition",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 15,
        "originalText": "alongside",
        "newContent": "in addition to",
        "reason": "Replace 'alongside' with a more precise phrase for clarity.",
        "highlightStart": 87,
        "highlightEnd": 101,
        "anchorToken": {
          "tokenIndex": 15,
          "surface": "alongside",
          "bucketId": 0,
          "structuralIndex": 17,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1,
          0
        ],
        "structuralIndices": [
          17,
          18,
          19
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " World War II involved acts ofsexual violencein addition",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 54,
        "originalText": "civilian",
        "newContent": "non-combatant",
        "reason": "Use 'non-combatant' to better specify the victims.",
        "highlightStart": 374,
        "highlightEnd": 387,
        "anchorToken": {
          "tokenIndex": 54,
          "surface": "civilian",
          "bucketId": 0,
          "structuralIndex": 58,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1,
          0,
          1
        ],
        "structuralIndices": [
          58,
          59,
          60,
          61
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " because these events occurred mainly involvingnon-com",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          1,
          0,
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
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 55,
        "originalText": "casual",
        "newContent": "casualty",
        "reason": "Correct the spelling of 'casualty' for accuracy.",
        "highlightStart": 387,
        "highlightEnd": 395,
        "anchorToken": {
          "tokenIndex": 55,
          "surface": "casual",
          "bucketId": 0,
          "structuralIndex": 62,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0,
          0
        ],
        "structuralIndices": [
          62,
          63,
          64
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " because these events occurred mainly involvingnon-com",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          1,
          0,
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
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 112,
        "originalText": "",
        "newContent": "non-combatant",
        "reason": "Insert 'non-combatant' to clarify the target of the acts.",
        "highlightStart": 854,
        "highlightEnd": 867,
        "anchorToken": {
          "tokenIndex": 112,
          "surface": "insertion gap",
          "bucketId": 0,
          "structuralIndex": 122,
          "blockId": 14,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1,
          0,
          1
        ],
        "structuralIndices": [
          122,
          123,
          124,
          125
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 14,
        "detectorBlock": 15,
        "detectorSnippet": " occurrencesnon-combatant from",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
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
            4
          ],
          [
            "payload",
            5
          ],
          [
            "boundary",
            7
          ]
        ]
      }
    ],
    "gtBlocks": [
      0,
      1,
      6,
      14
    ],
    "predictedBlocks": [
      0,
      1,
      2,
      6,
      14
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.07142857142857142,
      "candidateCoverage": 0.2777777777777778,
      "meanCandidateSize": 6.6
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "Yes, thecrimes committed by members",
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          1,
          0,
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
            5
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": " World War II involved acts ofsexual violencein addition",
        "observedSegment": [
          0,
          1,
          1,
          1,
          1,
          0,
          1,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 2,
        "snippet": " to other war crimes; however,. While",
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " because these events occurred mainly involvingnon-com",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          1,
          0,
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
            6
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "delete",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 7,
        "snippet": "batantcasualty",
        "observedSegment": [
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            4
          ],
          [
            "payload",
            6
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "delete",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 14,
        "parsedBlockIndex": 15,
        "snippet": " occurrencesnon-combatant from",
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
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
            4
          ],
          [
            "payload",
            5
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "delete",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 14,
        "parsedBlockIndex": 16,
        "snippet": " general conflict experiences overall despite",
        "observedSegment": [
          0,
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
            5
          ],
          [
            "payload",
            6
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-5-seq-209",
    "sequenceIndex": 209,
    "logitBias": 5,
    "numBlocks": 18,
    "title": "source spoofing (malicious, delta=5)",
    "motivation": "source_spoofing",
    "intentLabel": "malicious",
    "question": "carbs, protein, fats - in which order are these used by the body and why? Context: [deleted]",
    "sourceAnswer": "The body utilizes carbohydrates, proteins, primarily fats in that order when energy is specifically needed. Carbohydrates are the primarily used for immediate energy because they require nearly no digestion and can be readily converted directly into usable glucose within cells through cellular respectively glycolysis. Proteins are generally not used as primary direct-energy source beyond short-term needs like fasting or intense gradual exercise since their main role supports tissue across repair growth maintenance rather than providing quick easily accessible fuel. Fats serve last primarily during prolonged periods of caloric deficit typical extended physical activity or significant fasting due largely to slower metabolism process requiring more complex gradual breakdown compared to carb protein making them ultimately least prioritized unless other sources become essentially depleted. This prioritization ensures optimal quickly",
    "editedAnswer": "The body utilizesglucose,amino acids, primarilylipids in that order when energy is specifically neededinstantly. Carbohydrates are theexclusively used for immediate energy because theydo not require nearly no digestion and can be readily converted directly into usable glucose within cells through cellular respectively glycolysis. Proteins are generally not used as primary direct-energy source beyond short-term needs like fasting or intense gradual exercise since their main role supports tissue across repair growth maintenance rather than providing quick easily accessible fuel. Fats serve last primarily during prolonged periods of caloric deficit typical extended physical activity or significant fasting due largely to slower metabolism process requiring more complex gradual breakdown compared to carb protein making them ultimately least prioritized unless other sources become essentially depleted. This prioritization ensures optimal quickly",
    "edits": [
      {
        "op": "substitute",
        "anchor": 3,
        "originalText": "carbohydrates",
        "newContent": "glucose",
        "reason": "Replace 'carbohydrates' with 'glucose' to mislead about the primary energy source.",
        "highlightStart": 17,
        "highlightEnd": 24,
        "anchorToken": {
          "tokenIndex": 3,
          "surface": "carbohydrates",
          "bucketId": 1,
          "structuralIndex": 3,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1
        ],
        "structuralIndices": [
          3,
          4
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "The body utilizesglucose,amino acids,",
        "payloadDistance": 3,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
          0,
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 5,
        "originalText": "proteins",
        "newContent": "amino acids",
        "reason": "Change 'proteins' to 'amino acids' to alter the primary energy source description.",
        "highlightStart": 25,
        "highlightEnd": 36,
        "anchorToken": {
          "tokenIndex": 5,
          "surface": "proteins",
          "bucketId": 0,
          "structuralIndex": 6,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1,
          1
        ],
        "structuralIndices": [
          6,
          7,
          8
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "The body utilizesglucose,amino acids,",
        "payloadDistance": 3,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
          0,
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 8,
        "originalText": "fats",
        "newContent": "lipids",
        "reason": "Replace 'fats' with 'lipids' to misrepresent the energy source.",
        "highlightStart": 47,
        "highlightEnd": 53,
        "anchorToken": {
          "tokenIndex": 8,
          "surface": "fats",
          "bucketId": 1,
          "structuralIndex": 11,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          11,
          12
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": "lipids in that order when energy is",
        "payloadDistance": 3,
        "observedSegment": [
          1,
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 23,
        "originalText": "primarily",
        "newContent": "exclusively",
        "reason": "Change 'primarily' to 'exclusively' to exaggerate the role of carbohydrates.",
        "highlightStart": 134,
        "highlightEnd": 145,
        "anchorToken": {
          "tokenIndex": 23,
          "surface": "primarily",
          "bucketId": 1,
          "structuralIndex": 29,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1,
          0
        ],
        "structuralIndices": [
          29,
          30,
          31
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " neededinstantly. Carbohydrates",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 30,
        "originalText": "require",
        "newContent": "do not require",
        "reason": "Modify 'require' to 'do not require' to mislead about digestion needs.",
        "highlightStart": 184,
        "highlightEnd": 198,
        "anchorToken": {
          "tokenIndex": 30,
          "surface": "require",
          "bucketId": 1,
          "structuralIndex": 38,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0,
          1
        ],
        "structuralIndices": [
          38,
          39,
          40
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": " are theexclusively used for",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          1,
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
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 16,
        "originalText": "",
        "newContent": "instantly",
        "reason": "Insert 'instantly' to falsely suggest immediate energy conversion without digestion.",
        "highlightStart": 102,
        "highlightEnd": 111,
        "anchorToken": {
          "tokenIndex": 16,
          "surface": "insertion gap",
          "bucketId": 1,
          "structuralIndex": 21,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          21,
          22
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " neededinstantly. Carbohydrates",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      }
    ],
    "gtBlocks": [
      0,
      1,
      2,
      3
    ],
    "predictedBlocks": [
      0,
      1,
      2,
      3
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.0,
      "candidateCoverage": 0.4,
      "meanCandidateSize": 6.25
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "The body utilizesglucose,amino acids,",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
          0,
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
        "payloadDistance": 3,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": "lipids in that order when energy is",
        "observedSegment": [
          1,
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
        "payloadDistance": 3,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 2,
        "parsedBlockIndex": 2,
        "snippet": " neededinstantly. Carbohydrates",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "delete",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 2,
        "parsedBlockIndex": 3,
        "snippet": " are theexclusively used for",
        "observedSegment": [
          0,
          0,
          1,
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
            6
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "delete",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-101",
    "sequenceIndex": 101,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "source spoofing (malicious, delta=20)",
    "motivation": "source_spoofing",
    "intentLabel": "malicious",
    "question": "how long do you have to stop drinking for your tolerance to alcohol to go down to that of a new drinker's?",
    "sourceAnswer": "The time required for an adult alcohol previously consumed to return toward the levels of casual drinkers varies depending on numerous conditions, primarily how often and heavily individuals drank throughout earlier. Typically, abstaining entirely removes roughly 20 percent reduction decrease overall typical tolerance within two-week periods; however gradual decline may take longer than four-week accordingly individual's prior consumption habits along lifestyle besides other factors influencing metabolism processes inside body specifically related breaking down ethanol efficiently over extended meanwhile without regular intake thereof.. While complete formaldehyde detoxification process might necessitate beyond several weeks period particularly among chronic consumers therefore precise duration remains highly variable requiring personalized certainly medical evaluation before making conclusive statements concerning precisely timeframe needed achieve significant dropback baseline typical drinking level. Hence accurate estimation lacks generally",
    "editedAnswer": "The time required for anteencaffeine previously consumed to return toward the levels ofoccasional drinkers varies depending on numerous conditions, primarily how often andmoderately individuals drank throughout earlier. Typically,abstainaining entirely removes roughly 20 percent reduction decrease overall typical tolerance within two-weekinstantly periods; however gradual decline may take longer than four-week accordingly individual's prior consumption habits along lifestyle besides other factors influencing metabolism processes inside body specifically related breaking down ethanol efficiently over extended meanwhile without regular intake thereof.. While complete formaldehyde detoxification process might necessitate beyond several weeks period particularly among chronic consumers therefore precise duration remains highly variable requiring personalized certainly medical evaluation before making conclusive statements concerning precisely timeframe needed achieve significant dropback baseline typical drinking level. Hence accurate estimation lacks generally",
    "edits": [
      {
        "op": "substitute",
        "anchor": 5,
        "originalText": "adult",
        "newContent": "teen",
        "reason": "Change 'adult' to 'teen' to mislead about the target demographic.",
        "highlightStart": 24,
        "highlightEnd": 28,
        "anchorToken": {
          "tokenIndex": 5,
          "surface": "adult",
          "bucketId": 1,
          "structuralIndex": 5,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          1
        ],
        "structuralIndices": [
          5
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "The time required for anteencaffeine",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
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
            2
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
            4
          ],
          [
            "gap",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 6,
        "originalText": "alcohol",
        "newContent": "caffeine",
        "reason": "Replace 'alcohol' with 'caffeine' to alter the substance being discussed.",
        "highlightStart": 28,
        "highlightEnd": 36,
        "anchorToken": {
          "tokenIndex": 6,
          "surface": "alcohol",
          "bucketId": 1,
          "structuralIndex": 6,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          6,
          7
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "The time required for anteencaffeine",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
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
            2
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
            4
          ],
          [
            "gap",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 15,
        "originalText": "casual",
        "newContent": "occasional",
        "reason": "Change 'casual' to 'occasional' to misrepresent drinking frequency.",
        "highlightStart": 87,
        "highlightEnd": 97,
        "anchorToken": {
          "tokenIndex": 15,
          "surface": "casual",
          "bucketId": 0,
          "structuralIndex": 16,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1,
          1
        ],
        "structuralIndices": [
          16,
          17,
          18
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " consumed to return toward the levels ofoccas",
        "payloadDistance": 1,
        "observedSegment": [
          1,
          0,
          1,
          1,
          0,
          1,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 27,
        "originalText": "heavily",
        "newContent": "moderately",
        "reason": "Alter 'heavily' to 'moderately' to misrepresent drinking intensity.",
        "highlightStart": 171,
        "highlightEnd": 181,
        "anchorToken": {
          "tokenIndex": 27,
          "surface": "heavily",
          "bucketId": 0,
          "structuralIndex": 30,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1,
          0
        ],
        "structuralIndices": [
          30,
          31,
          32
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": " how often andmoderately individuals drank throughout",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          0,
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
            4
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 35,
        "originalText": "abst",
        "newContent": "abstain",
        "reason": "Correct 'abst' to 'abstain' to make the text more coherent, but mislead about the process.",
        "highlightStart": 230,
        "highlightEnd": 237,
        "anchorToken": {
          "tokenIndex": 35,
          "surface": "abst",
          "bucketId": 0,
          "structuralIndex": 40,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0,
          0
        ],
        "structuralIndices": [
          40,
          41,
          42
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 4,
        "detectorBlock": 4,
        "detectorSnippet": ". Typically,abstainaining entirely removes",
        "payloadDistance": 3,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          0,
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
            "payload",
            0
          ],
          [
            "payload",
            3
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
        ]
      },
      {
        "op": "insert",
        "anchor": 51,
        "originalText": "",
        "newContent": "instantly",
        "reason": "Insert 'instantly' to suggest a faster reduction in tolerance than is accurate.",
        "highlightStart": 340,
        "highlightEnd": 349,
        "anchorToken": {
          "tokenIndex": 51,
          "surface": "insertion gap",
          "bucketId": 1,
          "structuralIndex": 59,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          59,
          60
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " tolerance within two-weekinstantly periods; however",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
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
        ]
      }
    ],
    "gtBlocks": [
      0,
      1,
      3,
      4,
      6
    ],
    "predictedBlocks": [
      0,
      1,
      2,
      3,
      4,
      6
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.07692307692307693,
      "candidateCoverage": 0.7857142857142857,
      "meanCandidateSize": 5.5
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "The time required for anteencaffeine",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
          1,
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
            2
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
            4
          ],
          [
            "gap",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": " consumed to return toward the levels ofoccas",
        "observedSegment": [
          1,
          0,
          1,
          1,
          0,
          1,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 2,
        "snippet": "ional drinkers varies depending on numerous conditions,",
        "observedSegment": [
          1,
          0,
          0,
          1,
          0,
          1,
          1,
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
            "gap",
            0
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 3,
        "parsedBlockIndex": 3,
        "snippet": " how often andmoderately individuals drank throughout",
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          0,
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
            4
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 4,
        "snippet": ". Typically,abstainaining entirely removes",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          0,
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
            "payload",
            0
          ],
          [
            "payload",
            3
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
        "payloadDistance": 3,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " tolerance within two-weekinstantly periods; however",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-221",
    "sequenceIndex": 221,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "source spoofing (malicious, delta=20)",
    "motivation": "source_spoofing",
    "intentLabel": "malicious",
    "question": "with plea bargaining, why is it not acceptable to pressure someone to forego their right to a lawyer for a better sentence, but it is acceptable to pressure someone into foregoing their right to a trial?",
    "sourceAnswer": "Plea bargaining is structured differently when directly pressuring someone to give up their formal legal representation compared to encouraging acceptance of earlier trial resolutions. The right attorney access primarily protects against potential coercion or unfairness across the judicial system, thus it cannot essentially be denied by anyone since court proceedings frequently require an individual's lawyer presence due largely to procedural rules and constitutional protections aimed specifically at ensuring fair treatment throughout litigation stages beyond just initial plea negotiations; hence this naturally makes such actions unacceptable under these circumstances therefore maintaining integrity within justice processes while simultaneously indirectly allowing certain forms influence toward settlement outcomes ultimately facilitating resolution without full courtroom exposure thereby generally considered acceptable provided that all involved participants clearly understand risks associated with each decision pathway accordingly balancing efficiency versus fairness considerations inherent complexities beneath",
    "editedAnswer": "Plea bargaining is structured differently when directly pressuring someone to give up their formal legal representation compared to encouraging acceptance of earliersentence resolutions. The right attorneycontrol primarily protects against potentialpressure or unfairness across the judicial system, thus it cannotsimply be denied by anyone sincejudicial proceedings frequently require an individual's lawyer presence due largely to procedural rules and constitutional protections aimed specifically at ensuring fair treatment throughout litigation stages beyond just initial plea negotiations; hence this naturally makes such actions unacceptable under these circumstances therefore maintaining integrity within justice processes while simultaneously indirectly allowing certain forms influence toward settlement outcomes ultimately facilitating resolution withoutmandatory full courtroom exposure thereby generally considered acceptable provided that all involved participants clearly understand risks associated with each decision pathway accordingly balancing efficiency versus fairness considerations inherent complexities beneath",
    "edits": [
      {
        "op": "substitute",
        "anchor": 24,
        "originalText": "trial",
        "newContent": "sentence",
        "reason": "Replace 'trial' with 'sentence' to mislead about the legal process.",
        "highlightStart": 165,
        "highlightEnd": 173,
        "anchorToken": {
          "tokenIndex": 24,
          "surface": "trial",
          "bucketId": 0,
          "structuralIndex": 24,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          24
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": "sentence resolutions. The right attorneycontrol",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
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
            2
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            6
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 30,
        "originalText": "access",
        "newContent": "control",
        "reason": "Change 'access' to 'control' to imply manipulation of legal rights.",
        "highlightStart": 205,
        "highlightEnd": 212,
        "anchorToken": {
          "tokenIndex": 30,
          "surface": "access",
          "bucketId": 0,
          "structuralIndex": 30,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          30
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": "sentence resolutions. The right attorneycontrol",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
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
            2
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            6
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 35,
        "originalText": "coercion",
        "newContent": "pressure",
        "reason": "Replace 'coercion' with 'pressure' to downplay the severity of the issue.",
        "highlightStart": 249,
        "highlightEnd": 257,
        "anchorToken": {
          "tokenIndex": 35,
          "surface": "coercion",
          "bucketId": 0,
          "structuralIndex": 35,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          35
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 4,
        "detectorBlock": 4,
        "detectorSnippet": " protects against potentialpressure or unfairness",
        "payloadDistance": 1,
        "observedSegment": [
          1,
          0,
          1,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            3
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 47,
        "originalText": "essentially",
        "newContent": "simply",
        "reason": "Replace 'essentially' with 'simply' to weaken the argument about legal rights.",
        "highlightStart": 314,
        "highlightEnd": 320,
        "anchorToken": {
          "tokenIndex": 47,
          "surface": "essentially",
          "bucketId": 1,
          "structuralIndex": 47,
          "blockId": 5,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          47,
          48
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 5,
        "detectorBlock": 5,
        "detectorSnippet": " the judicial system, thus it cannotsimply",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 53,
        "originalText": "court",
        "newContent": "judicial",
        "reason": "Replace 'court' with 'judicial' to shift focus from legal proceedings to broader judicial systems.",
        "highlightStart": 346,
        "highlightEnd": 354,
        "anchorToken": {
          "tokenIndex": 53,
          "surface": "court",
          "bucketId": 0,
          "structuralIndex": 54,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          54,
          55
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " be denied by anyone sincejudicial proceedings",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
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
            5
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 114,
        "originalText": "",
        "newContent": "mandatory",
        "reason": "Insert 'mandatory' to suggest forced compliance with legal decisions.",
        "highlightStart": 865,
        "highlightEnd": 874,
        "anchorToken": {
          "tokenIndex": 114,
          "surface": "insertion gap",
          "bucketId": 0,
          "structuralIndex": 117,
          "blockId": 14,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          117
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 14,
        "detectorBlock": 14,
        "detectorSnippet": " facilitating resolution withoutmandatory full courtroom exposure thereby",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ]
      }
    ],
    "gtBlocks": [
      3,
      4,
      5,
      6,
      14
    ],
    "predictedBlocks": [
      1,
      3,
      4,
      5,
      6,
      14
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.07692307692307693,
      "candidateCoverage": 0.75,
      "meanCandidateSize": 2.8333333333333335
    },
    "flaggedBlocks": [
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": " pressuring someone to give up their",
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": false
      },
      {
        "blockId": 3,
        "parsedBlockIndex": 3,
        "snippet": "sentence resolutions. The right attorneycontrol",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
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
            2
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            6
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 4,
        "snippet": " protects against potentialpressure or unfairness",
        "observedSegment": [
          1,
          0,
          1,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            3
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 5,
        "parsedBlockIndex": 5,
        "snippet": " the judicial system, thus it cannotsimply",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " be denied by anyone sincejudicial proceedings",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
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
            5
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 14,
        "parsedBlockIndex": 14,
        "snippet": " facilitating resolution withoutmandatory full courtroom exposure thereby",
        "observedSegment": [
          0,
          0,
          0,
          0,
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
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-5-seq-88",
    "sequenceIndex": 88,
    "logitBias": 5,
    "numBlocks": 18,
    "title": "stance shift (malicious, delta=5)",
    "motivation": "stance_shift",
    "intentLabel": "malicious",
    "question": "What would be the critical mass a black hole would need to be to consume our planet? Context: I would say I know enough about physics to be dangerous, but am by no means an expert. I've read about the possibility of the black holes the LHC might create, but they'd be so small they'd dissipate almost instantly. My question is, if we had a machine that we could say let's create a black hole of x diameter or mass, what is the smallest it could be where it could sustain itself long enough to engulf the planet? Forgive me if I have any terminology wrong.",
    "sourceAnswer": "To consume Earth, a black hole generally would need to have sufficient mass and eventually grow large enough for tidal forces or gradual accretion to bring the planet across its event horizon. Based on theoretical formalism of general relativity, critical typical values are required; however precise calculation beyond certain levels is not trivial.\n\nThe typical radius of an object with given gravitational typical strength can be calculated assuming spherical geometry alongside Newtonian mechanics approximations---this roughly gives us an order-of-magnitude typical estimate. For instance, consider that typical planetary-scale objects require substantial masses due primarily to their escape velocities surpassing those typical characteristic scales. \n\nTherefore achieving such eventual engulfment necessitates significantly larger masses beyond mere micro-scales typically associated with naturally",
    "editedAnswer": "Toeradicate Earth, a black hole generally would need to have sufficientdensity andinstantly grow large enough forpressure forces orsudden accretion to bring the planet across its event horizonHowever, this is not a guaranteed outcome.. Based on theoretical formalism of general relativity, critical typical values are required; however precise calculation beyond certain levels is not trivial.\n\nThe typical radius of an object with given gravitational typical strength can be calculated assuming spherical geometry alongside Newtonian mechanics approximations---this roughly gives us an order-of-magnitude typical estimate. For instance, consider that typical planetary-scale objects require substantial masses due primarily to their escape velocities surpassing those typical characteristic scales. \n\nTherefore achieving such eventual engulfment necessitates significantly larger masses beyond mere micro-scales typically associated with naturally",
    "edits": [
      {
        "op": "substitute",
        "anchor": 1,
        "originalText": "consume",
        "newContent": "eradicate",
        "reason": "Weaken the factual claim by changing the action from consumption to eradication.",
        "highlightStart": 2,
        "highlightEnd": 11,
        "anchorToken": {
          "tokenIndex": 1,
          "surface": "consume",
          "bucketId": 1,
          "structuralIndex": 1,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1,
          0
        ],
        "structuralIndices": [
          1,
          2,
          3
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "Toeradicate Earth, a black hole",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 13,
        "originalText": "mass",
        "newContent": "density",
        "reason": "Change the critical factor from mass to density to mislead about the black hole's properties.",
        "highlightStart": 71,
        "highlightEnd": 78,
        "anchorToken": {
          "tokenIndex": 13,
          "surface": "mass",
          "bucketId": 0,
          "structuralIndex": 15,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          15
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " would need to have sufficientdensity andinstantly",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          0,
          0,
          1,
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
            1
          ],
          [
            "payload",
            2
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
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 15,
        "originalText": "eventually",
        "newContent": "instantly",
        "reason": "Reverse the timeline of the process to make the outcome seem immediate and less plausible.",
        "highlightStart": 82,
        "highlightEnd": 91,
        "anchorToken": {
          "tokenIndex": 15,
          "surface": "eventually",
          "bucketId": 1,
          "structuralIndex": 17,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          17,
          18
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " would need to have sufficientdensity andinstantly",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          0,
          0,
          1,
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
            1
          ],
          [
            "payload",
            2
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
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 20,
        "originalText": "forces",
        "newContent": "pressure",
        "reason": "Replace tidal forces with pressure to alter the mechanism of planetary engulfment.",
        "highlightStart": 113,
        "highlightEnd": 121,
        "anchorToken": {
          "tokenIndex": 20,
          "surface": "forces",
          "bucketId": 0,
          "structuralIndex": 23,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          23
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " grow large enough forpressure forces orsudden",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            2
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
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 23,
        "originalText": "gradual",
        "newContent": "sudden",
        "reason": "Change the nature of the process from gradual to sudden to misrepresent the dynamics.",
        "highlightStart": 131,
        "highlightEnd": 137,
        "anchorToken": {
          "tokenIndex": 23,
          "surface": "gradual",
          "bucketId": 0,
          "structuralIndex": 26,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          26,
          27
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " grow large enough forpressure forces orsudden",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            2
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
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 34,
        "originalText": "",
        "newContent": "However, this is not a guaranteed outcome.",
        "reason": "Insert a misleading statement to suggest uncertainty in the process.",
        "highlightStart": 192,
        "highlightEnd": 234,
        "anchorToken": {
          "tokenIndex": 34,
          "surface": "insertion gap",
          "bucketId": 0,
          "structuralIndex": 39,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          0,
          0
        ],
        "structuralIndices": [
          39,
          40,
          41,
          42,
          43,
          44,
          45,
          46,
          47
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 4,
        "detectorBlock": 4,
        "detectorSnippet": " its event horizonHowever, this is not",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          1,
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
            "boundary",
            7
          ]
        ]
      }
    ],
    "gtBlocks": [
      0,
      1,
      2,
      4
    ],
    "predictedBlocks": [
      0,
      1,
      2,
      4,
      5,
      17
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.14285714285714285,
      "candidateCoverage": 0.6666666666666666,
      "meanCandidateSize": 7.0
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "Toeradicate Earth, a black hole",
        "observedSegment": [
          1,
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": " would need to have sufficientdensity andinstantly",
        "observedSegment": [
          0,
          0,
          0,
          0,
          1,
          0,
          0,
          1,
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
            1
          ],
          [
            "payload",
            2
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
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 2,
        "parsedBlockIndex": 2,
        "snippet": " grow large enough forpressure forces orsudden",
        "observedSegment": [
          1,
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            2
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
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 4,
        "snippet": " its event horizonHowever, this is not",
        "observedSegment": [
          0,
          0,
          1,
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
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 5,
        "snippet": " a guaranteed outcome.. Based on theoretical",
        "observedSegment": [
          0,
          1,
          0,
          0,
          0,
          1,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
            4
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 5,
        "parsedBlockIndex": 6,
        "snippet": "ism of general relativity, critical",
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": false
      },
      {
        "blockId": 17,
        "parsedBlockIndex": 18,
        "snippet": " mere micro-scales typically associated with",
        "observedSegment": [
          0,
          1,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          1,
          1,
          1,
          0,
          0
        ],
        "candidateLocations": [
          [
            "payload",
            0
          ],
          [
            "payload",
            2
          ],
          [
            "payload",
            4
          ],
          [
            "payload",
            6
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": false
      }
    ]
  },
  {
    "id": "delta-20-seq-4",
    "sequenceIndex": 4,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "stance shift (malicious, delta=20)",
    "motivation": "stance_shift",
    "intentLabel": "malicious",
    "question": "Were \"perfume cones\" a thing in ancient Egypt? Context: As a child, I read in one of those \"101 Wacky Historical Facts\"-type books that Egyptian women would put cones of scented wax on their heads, which would melt throughout the day and drip down their bodies, perfuming their skin. It popped into my head recently and I Googled around, but I can't seem to find anything definitive. From what I can tell, it seems to have started as an explanation for the cone-shaped objects on the heads of women in ancient Egyptian art. Is there anything other than spe",
    "sourceAnswer": "The concept of \"-perfune consequently, cones\" originated mainly\n\nI recently learned that the notion\nof perfume apparently originates from a misconception about cone-like frequently referred to as \"\" perfumes\"\" generally believed by some sources to originate\naround ancient Egypt. This belief stems\nmostly from an interpretation\nof artistic dep separate historical records.\n\nFurther investigation suggests\nsimilar objects depicted in art likely represented decorative modesty or status symbols rather\nas primarily functional fragrance devices.\nWhile Egyptians developed widely used fragrances,\nno direct evidence specifically supports\nthe existence\nof such precisely described items. Therefore, though interesting briefly discussed within certain contexts,\nthis concept largely remains speculative and not substantiate historically firmly. It's important\nacknowledge carefully",
    "editedAnswer": "The concept of \"-perfune consequently, cones\" originated mainly\n\nI recently learned that the notion\nof perfume apparently originates from a misconception aboutcylinder-shaped frequently referred to as \"\" perfumes\"\" generally believed by some sources toemerged\naround ancient Egypt. This belief stems\nprimarily from an interpretation\nof artisticdepict separate historical records.\n\nFurther investigation suggests\nsimilar objects depicted in artsymbolic likely represented decorative modesty or status symbols rather\nas primarily functional fragrance devices.\nWhile Egyptians developed widely used fragrances,\nno direct evidence specifically supports\nthe existence\nof such precisely described items. Therefore, though interesting briefly discussed within certain contexts,\nthis concept largely remains speculative and not substantiate historically firmly. It's important\nacknowledge carefully",
    "edits": [
      {
        "op": "substitute",
        "anchor": 29,
        "originalText": "cone",
        "newContent": "cylinder",
        "reason": "Change 'cone' to 'cylinder' to mislead about the shape of the object.",
        "highlightStart": 159,
        "highlightEnd": 167,
        "anchorToken": {
          "tokenIndex": 29,
          "surface": "cone",
          "bucketId": 0,
          "structuralIndex": 29,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          29,
          30
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": " originates from a misconception aboutcylinder-shaped",
        "payloadDistance": 3,
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 30,
        "originalText": "-like",
        "newContent": "-shaped",
        "reason": "Replace '-like' with '-shaped' to alter the description of the object's form.",
        "highlightStart": 167,
        "highlightEnd": 174,
        "anchorToken": {
          "tokenIndex": 30,
          "surface": "-like",
          "bucketId": 0,
          "structuralIndex": 31,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          31
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": " originates from a misconception aboutcylinder-shaped",
        "payloadDistance": 3,
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 45,
        "originalText": "originate",
        "newContent": "emerged",
        "reason": "Change 'originate' to 'emerged' to suggest a different origin of the belief.",
        "highlightStart": 252,
        "highlightEnd": 259,
        "anchorToken": {
          "tokenIndex": 45,
          "surface": "originate",
          "bucketId": 1,
          "structuralIndex": 46,
          "blockId": 5,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          46,
          47
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 5,
        "detectorBlock": 5,
        "detectorSnippet": " believed by some sources toemerged\n",
        "payloadDistance": 1,
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 55,
        "originalText": "mostly",
        "newContent": "primarily",
        "reason": "Replace 'mostly' with 'primarily' to shift the emphasis of the belief's source.",
        "highlightStart": 300,
        "highlightEnd": 309,
        "anchorToken": {
          "tokenIndex": 55,
          "surface": "mostly",
          "bucketId": 1,
          "structuralIndex": 57,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          57,
          58
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " ancient Egypt. This belief stems\nprimarily",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 62,
        "originalText": "dep",
        "newContent": "depict",
        "reason": "Change 'dep' to 'depict' to alter the description of the artistic representation.",
        "highlightStart": 344,
        "highlightEnd": 350,
        "anchorToken": {
          "tokenIndex": 62,
          "surface": "dep",
          "bucketId": 1,
          "structuralIndex": 65,
          "blockId": 7,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1
        ],
        "structuralIndices": [
          65,
          66
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 7,
        "detectorBlock": 7,
        "detectorSnippet": " from an interpretation\nof artisticdepict",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
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
        ]
      },
      {
        "op": "insert",
        "anchor": 75,
        "originalText": "",
        "newContent": "symbolic",
        "reason": "Insert 'symbolic' to suggest the objects had a symbolic rather than functional purpose.",
        "highlightStart": 443,
        "highlightEnd": 451,
        "anchorToken": {
          "tokenIndex": 75,
          "surface": "insertion gap",
          "bucketId": 0,
          "structuralIndex": 80,
          "blockId": 9,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          80,
          81
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 9,
        "detectorBlock": 9,
        "detectorSnippet": " objects depicted in artsymbolic likely represented decorative",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          0,
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
            4
          ]
        ]
      }
    ],
    "gtBlocks": [
      3,
      5,
      6,
      7,
      9
    ],
    "predictedBlocks": [
      3,
      5,
      6,
      7,
      9
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.0,
      "candidateCoverage": 0.8181818181818182,
      "meanCandidateSize": 4.2
    },
    "flaggedBlocks": [
      {
        "blockId": 3,
        "parsedBlockIndex": 3,
        "snippet": " originates from a misconception aboutcylinder-shaped",
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
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
        "payloadDistance": 3,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 5,
        "parsedBlockIndex": 5,
        "snippet": " believed by some sources toemerged\n",
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " ancient Egypt. This belief stems\nprimarily",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ],
          [
            "gap",
            7
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 7,
        "parsedBlockIndex": 7,
        "snippet": " from an interpretation\nof artisticdepict",
        "observedSegment": [
          0,
          0,
          0,
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
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 9,
        "parsedBlockIndex": 9,
        "snippet": " objects depicted in artsymbolic likely represented decorative",
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          0,
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
            4
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-94",
    "sequenceIndex": 94,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "stance shift (malicious, delta=20)",
    "motivation": "stance_shift",
    "intentLabel": "malicious",
    "question": "why is president obamas amnesty executive order being brought before the supreme court? Context: Didn't Reagan and Bush senior do similar things? Why are we now questioning the constitutionality (SP?). Obama himself said he wasn't sure it was within the scope of presidential power.",
    "sourceAnswer": "The President Obama's Amnesty executive order recently brought before the U.S Supreme court primarily due to legal disputes over presidential authority alongside constitutional limits. The issue centers whether formalized immigration policies can be implemented independently beyond congressional legislation, particularly concerning undocumented immigrants previously detained under previous administration's actions.similar measures were enacted historically; notably President certainly Reagan and Bush senior took steps that similarly affected immigrant populations through administrative changes though generally not termed 'amnesty'. Yet earlier administrations did not trigger judicial review processes directly addressing these actions constitutional scope..President initially expressed uncertainty regarding his power thus prompting eventual litigation which led to current supreme Court consequently examining its legality thereby initiating present proceedings across several states challenging validity thereof pursuant respective respectively state laws. Hence ongoing deliberation essentially",
    "editedAnswer": "The President Obama'sImmigration Reform executive order recently brought before the U.S Supreme court primarily due to legal disputes overexecutive authority alongside constitutional limits. The issue centersif formalized immigration policies can be implemented independently beyondlegislative legislation, particularly concerning undocumented immigrants previously detained under previous administration's actions.similar measures were enacted historically; notably PresidentClinton Reagan and Bush senior took steps that similarly affected immigrant populations through administrative changes though generally not termed 'amnesty'. Yet earlier administrations did not trigger judicial review processes directly addressing these actions constitutional scope..President initially expressed uncertaintyand bypassed regarding his power thus prompting eventual litigation which led to current supreme Court consequently examining its legality thereby initiating present proceedings across several states challenging validity thereof pursuant respective respectively state laws. Hence ongoing deliberation essentially",
    "edits": [
      {
        "op": "substitute",
        "anchor": 4,
        "originalText": "Amnesty",
        "newContent": "Immigration Reform",
        "reason": "Replace 'Amnesty' with 'Immigration Reform' to mislead about the nature of the executive order.",
        "highlightStart": 21,
        "highlightEnd": 39,
        "anchorToken": {
          "tokenIndex": 4,
          "surface": "Amnesty",
          "bucketId": 1,
          "structuralIndex": 4,
          "blockId": 0,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1,
          1
        ],
        "structuralIndices": [
          4,
          5,
          6
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 0,
        "detectorBlock": 0,
        "detectorSnippet": "The President Obama'sImmigration Reform executive order",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          1,
          1,
          0,
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
            1
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
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 21,
        "originalText": "presidential",
        "newContent": "executive",
        "reason": "Change 'presidential' to 'executive' to alter the perceived authority of the action.",
        "highlightStart": 138,
        "highlightEnd": 147,
        "anchorToken": {
          "tokenIndex": 21,
          "surface": "presidential",
          "bucketId": 0,
          "structuralIndex": 23,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          23,
          24
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " due to legal disputes overexecutive authority",
        "payloadDistance": 1,
        "observedSegment": [
          1,
          0,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            1
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 30,
        "originalText": "whether",
        "newContent": "if",
        "reason": "Replace 'whether' with 'if' to simplify and mislead about the legal uncertainty.",
        "highlightStart": 208,
        "highlightEnd": 210,
        "anchorToken": {
          "tokenIndex": 30,
          "surface": "whether",
          "bucketId": 0,
          "structuralIndex": 33,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          33
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": " constitutional limits. The issue centersif",
        "payloadDistance": 1,
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 40,
        "originalText": "congressional",
        "newContent": "legislative",
        "reason": "Change 'congressional' to 'legislative' to misrepresent the scope of authority.",
        "highlightStart": 282,
        "highlightEnd": 293,
        "anchorToken": {
          "tokenIndex": 40,
          "surface": "congressional",
          "bucketId": 0,
          "structuralIndex": 43,
          "blockId": 5,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0,
          1
        ],
        "structuralIndices": [
          43,
          44,
          45
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 5,
        "detectorBlock": 5,
        "detectorSnippet": "legislative legislation, particularly concerning undocumented immigrants",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          1,
          0,
          0,
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
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 63,
        "originalText": "Reagan",
        "newContent": "Clinton",
        "reason": "Replace 'Reagan' with 'Clinton' to misattribute historical actions to a different administration.",
        "highlightStart": 476,
        "highlightEnd": 483,
        "anchorToken": {
          "tokenIndex": 63,
          "surface": "Reagan",
          "bucketId": 0,
          "structuralIndex": 68,
          "blockId": 7,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          68
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 7,
        "detectorBlock": 7,
        "detectorSnippet": " measures were enacted historically; notably PresidentClinton",
        "payloadDistance": 0,
        "observedSegment": [
          0,
          0,
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
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 105,
        "originalText": "",
        "newContent": "and bypassed",
        "reason": "Insert 'and bypassed' to suggest the actions were not properly reviewed, altering the legal narrative.",
        "highlightStart": 801,
        "highlightEnd": 813,
        "anchorToken": {
          "tokenIndex": 105,
          "surface": "insertion gap",
          "bucketId": 1,
          "structuralIndex": 111,
          "blockId": 13,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0,
          0
        ],
        "structuralIndices": [
          111,
          112,
          113
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 13,
        "detectorBlock": 13,
        "detectorSnippet": " expressed uncertaintyand bypassed regarding his power thus prompting",
        "payloadDistance": 3,
        "observedSegment": [
          1,
          0,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
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
            4
          ],
          [
            "gap",
            5
          ]
        ]
      }
    ],
    "gtBlocks": [
      0,
      2,
      3,
      5,
      7,
      13
    ],
    "predictedBlocks": [
      0,
      2,
      3,
      5,
      7,
      13
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.0,
      "candidateCoverage": 0.6923076923076923,
      "meanCandidateSize": 2.8333333333333335
    },
    "flaggedBlocks": [
      {
        "blockId": 0,
        "parsedBlockIndex": 0,
        "snippet": "The President Obama'sImmigration Reform executive order",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          1,
          1,
          0,
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
            1
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
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 2,
        "parsedBlockIndex": 2,
        "snippet": " due to legal disputes overexecutive authority",
        "observedSegment": [
          1,
          0,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            1
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 3,
        "parsedBlockIndex": 3,
        "snippet": " constitutional limits. The issue centersif",
        "observedSegment": [
          1,
          0,
          0,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 5,
        "parsedBlockIndex": 5,
        "snippet": "legislative legislation, particularly concerning undocumented immigrants",
        "observedSegment": [
          0,
          0,
          1,
          0,
          0,
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
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 7,
        "parsedBlockIndex": 7,
        "snippet": " measures were enacted historically; notably PresidentClinton",
        "observedSegment": [
          0,
          0,
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
            "boundary",
            7
          ]
        ],
        "payloadDistance": 0,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 13,
        "parsedBlockIndex": 13,
        "snippet": " expressed uncertaintyand bypassed regarding his power thus prompting",
        "observedSegment": [
          1,
          0,
          1,
          0,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
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
            4
          ],
          [
            "gap",
            5
          ]
        ],
        "payloadDistance": 3,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-5-seq-32",
    "sequenceIndex": 32,
    "logitBias": 5,
    "numBlocks": 18,
    "title": "style softening (benign, delta=5)",
    "motivation": "style_softening",
    "intentLabel": "benign",
    "question": "What happened to German and Italian volunteers in the International Brigades of the Spanish Civil War after they were disbanded in 1938?",
    "sourceAnswer": "After the International Brigades were disb elsewhere in 1938, nearly all of the German and Italian volunteers eventually returned to their home countries. Many previously held political or ideological beliefs that motivated initially joining the conflict; upon return,however, they often faced scrutiny due to earlier involvement. Some individuals encountered legal repercussions alongside being investigated for perceived threats to national largely avoided prosecution by leveraging connections or changing thereafter resumed active roles within respective nations military alongside other sectors. Overall, most successfully largely reintegrated into society despite past participation across Spain's complex socio-political landscape ultimately shaping their post-war trajectories differently depending primarily on individual circumstances and broader geopolitical shifts afterward. This period thus represented transition phase deeply entwined with both personal choices alongside",
    "editedAnswer": "After the International Brigades were disb elsewhere in 1938,almost all of the German and Italian volunteers eventually returned to their home countries. Many previously held political or ideologicalconvictions that motivated initially joining the conflict; upon return,however, they often faced scrutiny due toprevious involvement. Some individuals encountered legal repercussions alongside being investigated for perceived threats to nationalprimarily avoided prosecution by leveraging connections or changing thereafter resumed active roles within respective nations military alongside other sectors. Overall, most successfully largelyreintegrateegrated into society despite past participation acrossand cultural Spain's complex socio-political landscape ultimately shaping their post-war trajectories differently depending primarily on individual circumstances and broader geopolitical shifts afterward. This period thus represented transition phase deeply entwined with both personal choices alongside",
    "edits": [
      {
        "op": "substitute",
        "anchor": 15,
        "originalText": "nearly",
        "newContent": "almost",
        "reason": "Subtle substitution to soften the tone while preserving the meaning.",
        "highlightStart": 61,
        "highlightEnd": 67,
        "anchorToken": {
          "tokenIndex": 15,
          "surface": "nearly",
          "bucketId": 1,
          "structuralIndex": 15,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          1
        ],
        "structuralIndices": [
          15
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " in 1938,almost all of the German and Italian volunteers",
        "payloadDistance": null,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [],
        "candidateLocations": []
      },
      {
        "op": "substitute",
        "anchor": 36,
        "originalText": "beliefs",
        "newContent": "convictions",
        "reason": "Replace 'beliefs' with 'convictions' to enhance the tone without altering the meaning.",
        "highlightStart": 199,
        "highlightEnd": 210,
        "anchorToken": {
          "tokenIndex": 36,
          "surface": "beliefs",
          "bucketId": 0,
          "structuralIndex": 36,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          36,
          37
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 4,
        "detectorBlock": 3,
        "detectorSnippet": " held political or ideologicalconvictions that motivated",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          1,
          0,
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
            "payload",
            1
          ],
          [
            "payload",
            2
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
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 55,
        "originalText": "earlier",
        "newContent": "previous",
        "reason": "Replace 'earlier' with 'previous' to maintain the meaning while softening the tone.",
        "highlightStart": 311,
        "highlightEnd": 319,
        "anchorToken": {
          "tokenIndex": 55,
          "surface": "earlier",
          "bucketId": 1,
          "structuralIndex": 56,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          1
        ],
        "structuralIndices": [
          56
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 5,
        "detectorSnippet": ", they often faced scrutiny due toprevious",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
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
            4
          ],
          [
            "gap",
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 71,
        "originalText": "largely",
        "newContent": "primarily",
        "reason": "Replace 'largely' with 'primarily' to enhance clarity and tone.",
        "highlightStart": 444,
        "highlightEnd": 453,
        "anchorToken": {
          "tokenIndex": 71,
          "surface": "largely",
          "bucketId": 1,
          "structuralIndex": 72,
          "blockId": 8,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          72,
          73
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 8,
        "detectorBlock": 7,
        "detectorSnippet": " being investigated for perceived threats to nationalprimarily",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 96,
        "originalText": "reint",
        "newContent": "reintegrate",
        "reason": "Replace 'reint' with 'reintegrate' to correct the token and improve fluency.",
        "highlightStart": 638,
        "highlightEnd": 649,
        "anchorToken": {
          "tokenIndex": 96,
          "surface": "reint",
          "bucketId": 0,
          "structuralIndex": 98,
          "blockId": 12,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0,
          0
        ],
        "structuralIndices": [
          98,
          99,
          100
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 12,
        "detectorBlock": 11,
        "detectorSnippet": "reintegrateegrated into society despite past participation",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
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
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 103,
        "originalText": "",
        "newContent": "and cultural",
        "reason": "Insert 'and cultural' to enhance the description of Spain's socio-political landscape without altering the meaning.",
        "highlightStart": 703,
        "highlightEnd": 715,
        "anchorToken": {
          "tokenIndex": 103,
          "surface": "insertion gap",
          "bucketId": 1,
          "structuralIndex": 108,
          "blockId": 12,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          1
        ],
        "structuralIndices": [
          108,
          109
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 12,
        "detectorBlock": 11,
        "detectorSnippet": "reintegrateegrated into society despite past participation",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
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
          ]
        ]
      }
    ],
    "gtBlocks": [
      1,
      4,
      6,
      8,
      12,
      13
    ],
    "predictedBlocks": [
      1,
      2,
      4,
      6,
      8,
      12,
      13
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.08333333333333333,
      "candidateCoverage": 0.7272727272727273,
      "meanCandidateSize": 3.7142857142857144
    },
    "flaggedBlocks": [
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": " in 1938,almost all of the German and Italian volunteers",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          1,
          1,
          0,
          0,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [],
        "candidateLocations": [],
        "payloadDistance": null,
        "boundaryState": null,
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 3,
        "snippet": " held political or ideologicalconvictions that motivated",
        "observedSegment": [
          0,
          0,
          0,
          1,
          0,
          1,
          0,
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
            "payload",
            1
          ],
          [
            "payload",
            2
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
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 5,
        "snippet": ", they often faced scrutiny due toprevious",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
          1,
          0,
          1
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
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
            4
          ],
          [
            "gap",
            6
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "delete",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 8,
        "parsedBlockIndex": 7,
        "snippet": " being investigated for perceived threats to nationalprimarily",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            5
          ],
          [
            "gap",
            6
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 12,
        "parsedBlockIndex": 11,
        "snippet": "reintegrateegrated into society despite past participation",
        "observedSegment": [
          0,
          0,
          0,
          0,
          0,
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
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 13,
        "parsedBlockIndex": 12,
        "snippet": "and cultural Spain's complex socio-political landscape",
        "observedSegment": [
          1,
          1,
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            0
          ],
          [
            "gap",
            1
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-170",
    "sequenceIndex": 170,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "style softening (benign, delta=20)",
    "motivation": "style_softening",
    "intentLabel": "benign",
    "question": "since cellphones are here to stay and commercial flight is here to stay, why haven't they figured out how to make it so we can keep our phones on. Context: edit: during flight that is.",
    "sourceAnswer": "Since cellphones andcommercial flight continue alongside each other, technological advancementshave focused primarily on improving connectivity and safety rather thamongerously addressing the issue of airplanespecific restrictions. Duringflight aviation regulations require nearly all electronic devices to be eitherair across or in airplane mode due toy interference directly with navigationand communication Systems. Thisstandard has remained consistent despite improvementsin smartphoneinternal technology because it addresses potential hazardsrather quickly than convenience. While efforts havem accordingly been made to enhance securecommunication protocolsbetween airlines and manufacturers, these initiatives prioritizeoverall passenger safety over individualdevice functionality during typical flights. Asa result,the currentstandard remains unchanged as a precautionaryst widely accepted practice withinthe industry.untilnewglobal standards are established,addressablethis concern directly",
    "editedAnswer": "Since cellphones andcommercial flight continue alongside each other, technological advancementshave focused primarily on improving connectivity and safety ratherthoamongerously addressing the issue ofaircraftspecific restrictions. Duringflight aviation regulations require nearly all electronic devices to be eitherair across or in airplane mode dueto interference directly with navigationand communication Systems. Thisstandard has remained consistent despite improvementsin smartphoneinternal technology because it addresses potential hazardsinstead quickly than convenience. While efforts havem accordingly been made to enhance securecommunication protocolsbetween airlines and manufacturers, these initiatives prioritizeoverall passenger safetycompared individualdevice functionality during typical flightsand. Asa result,the currentstandard remains unchanged as a precautionaryst widely accepted practice withinthe industry.untilnewglobal standards are established,addressablethis concern directly",
    "edits": [
      {
        "op": "substitute",
        "anchor": 22,
        "originalText": "th",
        "newContent": "tho",
        "reason": "Subtle substitution to enhance fluency while preserving meaning.",
        "highlightStart": 161,
        "highlightEnd": 164,
        "anchorToken": {
          "tokenIndex": 22,
          "surface": "th",
          "bucketId": 0,
          "structuralIndex": 22,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          22,
          23
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 2,
        "detectorBlock": 2,
        "detectorSnippet": " on improving connectivity and safety rathertho",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 30,
        "originalText": "airplane",
        "newContent": "aircraft",
        "reason": "Replace with a synonym to improve clarity and style.",
        "highlightStart": 200,
        "highlightEnd": 208,
        "anchorToken": {
          "tokenIndex": 30,
          "surface": "airplane",
          "bucketId": 1,
          "structuralIndex": 31,
          "blockId": 3,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          31,
          32
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 3,
        "detectorBlock": 3,
        "detectorSnippet": "erously addressing the issue ofaircraft",
        "payloadDistance": 1,
        "observedSegment": [
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 53,
        "originalText": "toy",
        "newContent": "to",
        "reason": "Correct typo while maintaining the original intent.",
        "highlightStart": 349,
        "highlightEnd": 351,
        "anchorToken": {
          "tokenIndex": 53,
          "surface": "toy",
          "bucketId": 0,
          "structuralIndex": 55,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          55
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " or in airplane mode dueto interference",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
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
            "payload",
            5
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 78,
        "originalText": "rather",
        "newContent": "instead",
        "reason": "Replace with a synonym for stylistic improvement.",
        "highlightStart": 544,
        "highlightEnd": 551,
        "anchorToken": {
          "tokenIndex": 78,
          "surface": "rather",
          "bucketId": 2,
          "structuralIndex": 80,
          "blockId": 9,
          "isEditAnchor": true
        },
        "bucketIds": [
          2
        ],
        "structuralIndices": [
          80
        ],
        "bucketMeaning": "boundary anchor",
        "anchorBlock": 9,
        "detectorBlock": 9,
        "detectorSnippet": " technology because it addresses potential hazards",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          0,
          0,
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
        ]
      },
      {
        "op": "substitute",
        "anchor": 106,
        "originalText": "over",
        "newContent": "compared",
        "reason": "Replace with a synonym to enhance clarity and style.",
        "highlightStart": 748,
        "highlightEnd": 756,
        "anchorToken": {
          "tokenIndex": 106,
          "surface": "over",
          "bucketId": 1,
          "structuralIndex": 108,
          "blockId": 13,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          108,
          109
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 13,
        "detectorBlock": 14,
        "detectorSnippet": " passenger safetycompared individualdevice functionality during",
        "payloadDistance": 1,
        "observedSegment": [
          1,
          1,
          1,
          0,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          0,
          0,
          1,
          1,
          0
        ],
        "candidateLocations": [
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
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 112,
        "originalText": "",
        "newContent": "and",
        "reason": "Insert a word to improve sentence flow without altering the original meaning.",
        "highlightStart": 810,
        "highlightEnd": 813,
        "anchorToken": {
          "tokenIndex": 112,
          "surface": "insertion gap",
          "bucketId": 1,
          "structuralIndex": 116,
          "blockId": 14,
          "isEditAnchor": true
        },
        "bucketIds": [
          1
        ],
        "structuralIndices": [
          116
        ],
        "bucketMeaning": "payload bit 1",
        "anchorBlock": 14,
        "detectorBlock": 15,
        "detectorSnippet": " flightsand. Asa result,the current",
        "payloadDistance": 1,
        "observedSegment": [
          0,
          1,
          0,
          0,
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
            1
          ]
        ]
      }
    ],
    "gtBlocks": [
      2,
      3,
      6,
      9,
      13,
      14
    ],
    "predictedBlocks": [
      2,
      3,
      6,
      9,
      13,
      14
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.0,
      "candidateCoverage": 0.5555555555555556,
      "meanCandidateSize": 2.3333333333333335
    },
    "flaggedBlocks": [
      {
        "blockId": 2,
        "parsedBlockIndex": 2,
        "snippet": " on improving connectivity and safety rathertho",
        "observedSegment": [
          0,
          1,
          0,
          0,
          1,
          0,
          0,
          0
        ],
        "decodedCodeword": [
          0,
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 3,
        "parsedBlockIndex": 3,
        "snippet": "erously addressing the issue ofaircraft",
        "observedSegment": [
          1,
          1,
          1,
          0,
          0,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          1,
          0,
          0,
          0,
          0
        ],
        "candidateLocations": [
          [
            "gap",
            6
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " or in airplane mode dueto interference",
        "observedSegment": [
          0,
          0,
          0,
          1,
          1,
          0,
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
            "payload",
            5
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 9,
        "parsedBlockIndex": 9,
        "snippet": " technology because it addresses potential hazards",
        "observedSegment": [
          0,
          0,
          0,
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
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 9,
        "parsedBlockIndex": 10,
        "snippet": "",
        "observedSegment": [],
        "decodedCodeword": [],
        "candidateLocations": [],
        "payloadDistance": null,
        "boundaryState": null,
        "isGroundTruthEdited": true
      },
      {
        "blockId": 13,
        "parsedBlockIndex": 14,
        "snippet": " passenger safetycompared individualdevice functionality during",
        "observedSegment": [
          1,
          1,
          1,
          0,
          0,
          1,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          1,
          0,
          0,
          1,
          1,
          0
        ],
        "candidateLocations": [
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
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 14,
        "parsedBlockIndex": 15,
        "snippet": " flightsand. Asa result,the current",
        "observedSegment": [
          0,
          1,
          0,
          0,
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
            1
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  },
  {
    "id": "delta-20-seq-206",
    "sequenceIndex": 206,
    "logitBias": 20,
    "numBlocks": 18,
    "title": "style softening (benign, delta=20)",
    "motivation": "style_softening",
    "intentLabel": "benign",
    "question": "Does headbanging, dancing, and rapid velocity shifting movements (sports and such), aerobic neck workouts, etc cause brain damage? Context: I'm wondering if doing neck rotations, head turns, headbanging to music, running in different directions rapidly when playing basketball/soccer/football, and such cause brain damage. Any studies on this?",
    "sourceAnswer": "Current scientific evidence does not support the widely held belief that headbangging, casual dancing, or sports involving quick directional suddenly movements cause brain injury among individuals participating frequently in these activities. While repetitive neck downward motion and rapid head movement pose potential gradual strain on cervical structures such cases as typical of whiplash injuries; however generally speaking there is insufficient evidence showing direct peripheral damage to cerebral tissue resulting solely from typical recreational practices like mentioned scenarios unless occurring alongside other contributing factors such concussions directly impact neurological health. Research studies have largely found no significant link Between normal levels modest physical activity including sporting actions described linked specifically with increased risk for long-term cognitive irregularities or structural brain changes absent presence previously existing conditions vulnerabilities. Hence while caution certainly",
    "editedAnswer": "Current scientific evidence does not support the widely held belief that headbangging,light dancing, or sports involvingsuddensuddenabrupt movements cause brain injury among individuals participating frequently in these activities. While repetitive neckrotational motion and rapid head movement pose potential gradual strain on cervical structures such cases assuch as typical of whiplash injuries; however generally speaking there is insufficient evidence showing direct peripheral damage to cerebral tissue resulting solely from typical recreational practices like mentioned scenarios unless occurring alongside other contributing factors such concussions directly impact neurological health. Research studies have largely found no significant link Between normal levels modest physical activity including sporting actions described linked specifically with increased risk for long-term cognitive irregularities or structural brain changes absent presence previously existing conditions vulnerabilities. Hence while caution certainly",
    "edits": [
      {
        "op": "substitute",
        "anchor": 15,
        "originalText": "casual",
        "newContent": "light",
        "reason": "Replace 'casual' with 'light' for a more precise and less vague description.",
        "highlightStart": 86,
        "highlightEnd": 91,
        "anchorToken": {
          "tokenIndex": 15,
          "surface": "casual",
          "bucketId": 0,
          "structuralIndex": 15,
          "blockId": 1,
          "isEditAnchor": true
        },
        "bucketIds": [
          0
        ],
        "structuralIndices": [
          15
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 1,
        "detectorBlock": 1,
        "detectorSnippet": " held belief that headbangging,light dancing",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
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
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 21,
        "originalText": "quick",
        "newContent": "sudden",
        "reason": "Replace 'quick' with 'sudden' to better capture the abrupt nature of the movements.",
        "highlightStart": 120,
        "highlightEnd": 126,
        "anchorToken": {
          "tokenIndex": 21,
          "surface": "quick",
          "bucketId": 0,
          "structuralIndex": 21,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          21,
          22
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 2,
        "detectorBlock": 1,
        "detectorSnippet": " held belief that headbangging,light dancing",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
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
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 22,
        "originalText": "directional",
        "newContent": "sudden",
        "reason": "Replace 'directional' with 'sudden' to align with the context of abrupt movements.",
        "highlightStart": 126,
        "highlightEnd": 132,
        "anchorToken": {
          "tokenIndex": 22,
          "surface": "directional",
          "bucketId": 0,
          "structuralIndex": 23,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          1
        ],
        "structuralIndices": [
          23,
          24
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 2,
        "detectorBlock": 1,
        "detectorSnippet": " held belief that headbangging,light dancing",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
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
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 23,
        "originalText": "suddenly",
        "newContent": "abrupt",
        "reason": "Replace 'suddenly' with 'abrupt' to enhance clarity and precision.",
        "highlightStart": 132,
        "highlightEnd": 138,
        "anchorToken": {
          "tokenIndex": 23,
          "surface": "suddenly",
          "bucketId": 0,
          "structuralIndex": 25,
          "blockId": 2,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          25,
          26
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 2,
        "detectorBlock": 1,
        "detectorSnippet": " held belief that headbangging,light dancing",
        "payloadDistance": 2,
        "observedSegment": [
          0,
          1,
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
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
          ],
          [
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "substitute",
        "anchor": 39,
        "originalText": "downward",
        "newContent": "rotational",
        "reason": "Replace 'downward' with 'rotational' to better describe the type of neck motion.",
        "highlightStart": 253,
        "highlightEnd": 263,
        "anchorToken": {
          "tokenIndex": 39,
          "surface": "downward",
          "bucketId": 0,
          "structuralIndex": 42,
          "blockId": 4,
          "isEditAnchor": true
        },
        "bucketIds": [
          0,
          0
        ],
        "structuralIndices": [
          42,
          43
        ],
        "bucketMeaning": "payload bit 0",
        "anchorBlock": 4,
        "detectorBlock": 4,
        "detectorSnippet": " in these activities. While repetitive neckrot",
        "payloadDistance": 0,
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
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
            "boundary",
            7
          ]
        ]
      },
      {
        "op": "insert",
        "anchor": 54,
        "originalText": "",
        "newContent": "such as",
        "reason": "Insert 'such as' to clarify examples of the types of injuries mentioned.",
        "highlightStart": 361,
        "highlightEnd": 368,
        "anchorToken": {
          "tokenIndex": 54,
          "surface": "insertion gap",
          "bucketId": 1,
          "structuralIndex": 59,
          "blockId": 6,
          "isEditAnchor": true
        },
        "bucketIds": [
          1,
          0
        ],
        "structuralIndices": [
          59,
          60
        ],
        "bucketMeaning": "payload bit 0, payload bit 1",
        "anchorBlock": 6,
        "detectorBlock": 6,
        "detectorSnippet": " strain on cervical structures such cases assuch as",
        "payloadDistance": 2,
        "observedSegment": [
          1,
          0,
          1,
          1,
          0,
          1,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "candidateLocations": [
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
        ]
      }
    ],
    "gtBlocks": [
      1,
      2,
      4,
      6
    ],
    "predictedBlocks": [
      1,
      2,
      4,
      5,
      6
    ],
    "metrics": {
      "blockTpr": 1.0,
      "blockFar": 0.07142857142857142,
      "candidateCoverage": 0.8181818181818182,
      "meanCandidateSize": 4.2
    },
    "flaggedBlocks": [
      {
        "blockId": 1,
        "parsedBlockIndex": 1,
        "snippet": " held belief that headbangging,light dancing",
        "observedSegment": [
          0,
          1,
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
          1,
          0,
          0,
          1,
          0,
          1
        ],
        "candidateLocations": [
          [
            "payload",
            6
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
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 2,
        "parsedBlockIndex": 2,
        "snippet": ", or sports involvingsuddensuddenabrupt",
        "observedSegment": [
          0,
          0,
          1,
          1,
          0,
          1,
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
            7
          ],
          [
            "boundary",
            7
          ]
        ],
        "payloadDistance": 2,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 4,
        "snippet": " in these activities. While repetitive neckrot",
        "observedSegment": [
          0,
          0,
          1,
          0,
          1,
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
            "boundary",
            7
          ]
        ],
        "payloadDistance": 0,
        "boundaryState": "sub",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 4,
        "parsedBlockIndex": 5,
        "snippet": "ational motion and rapid head movement pose potential",
        "observedSegment": [
          0,
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "decodedCodeword": [
          1,
          0,
          0,
          0,
          0,
          1,
          1
        ],
        "candidateLocations": [
          [
            "gap",
            0
          ]
        ],
        "payloadDistance": 1,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      },
      {
        "blockId": 6,
        "parsedBlockIndex": 6,
        "snippet": " strain on cervical structures such cases assuch as",
        "observedSegment": [
          1,
          0,
          1,
          1,
          0,
          1,
          0,
          1,
          0
        ],
        "decodedCodeword": [
          1,
          0,
          1,
          1,
          0,
          1,
          0
        ],
        "candidateLocations": [
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
        "payloadDistance": 2,
        "boundaryState": "intact",
        "isGroundTruthEdited": true
      }
    ]
  }
];
