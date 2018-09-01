(define (domain pr2-tamp)
  (:requirements :strips :equality)
  (:predicates
    (Arm ?a)
    (Stackable ?o ?r)
    (Sink ?r)
    (Stove ?r)

    (Grasp ?o ?g)
    (Kin ?a ?o ?p ?g ?q ?t)
    (BaseMotion ?q1 ?t ?q2)
    (Supported ?o ?p ?r)

    (TrajPoseCollision ?t ?o ?p)
    (TrajArmCollision ?t ?a ?q)
    (TrajGraspCollision ?t ?a ?o ?g)

    (AtPose ?o ?p)
    (AtGrasp ?a ?o ?g)
    (HandEmpty ?a)
    (AtBConf ?q)
    (AtAConf ?a ?q)
    (CanMove)
    (Cleaned ?o)
    (Cooked ?o)

    (On ?o ?r)
    (Holding ?a ?o)
    (UnsafeBTraj ?t)
  )
  (:functions
    (MoveCost ?t)
    (PickCost)
    (PlaceCost)
  )

  (:action move_base
    :parameters (?q1 ?q2 ?t)
    :precondition (and (BaseMotion ?q1 ?t ?q2)
                       (AtBConf ?q1) (CanMove) (not (UnsafeBTraj ?t)))
    :effect (and (AtBConf ?q2)
                 (not (AtBConf ?q1)) (not (CanMove))
                 (increase (total-cost) (MoveCost ?t)))
  )
  (:action pick
    :parameters (?a ?o ?p ?g ?q ?t)
    :precondition (and (Kin ?a ?o ?p ?g ?q ?t)
                       (AtPose ?o ?p) (HandEmpty ?a) (AtBConf ?q))
    :effect (and (AtGrasp ?a ?o ?g) (CanMove)
                 (not (AtPose ?o ?p)) (not (HandEmpty ?a))
                 (increase (total-cost) (PickCost)))
  )
  (:action place
    :parameters (?a ?o ?p ?g ?q ?t)
    :precondition (and (Kin ?a ?o ?p ?g ?q ?t)
                       (AtGrasp ?a ?o ?g) (AtBConf ?q))
    :effect (and (AtPose ?o ?p) (HandEmpty ?a) (CanMove)
                 (not (AtGrasp ?a ?o ?g))
                 (increase (total-cost) (PlaceCost)))
  )

  (:action clean
    :parameters (?o ?r)
    :precondition (and (Stackable ?o ?r) (Sink ?r)
                       (On ?o ?r))
    :effect (Cleaned ?o)
  )
  (:action cook
    :parameters (?o ?r)
    :precondition (and (Stackable ?o ?r) (Stove ?r)
                       (On ?o ?r) (Cleaned ?o))
    :effect (and (Cooked ?o)
                 (not (Cleaned ?o)))
  )

  (:derived (On ?o ?r)
    (exists (?p) (and (Supported ?o ?p ?r)
                      (AtPose ?o ?p)))
  )
  (:derived (Holding ?a ?o)
    (exists (?g) (and (Arm ?a) (Grasp ?o ?g)
                      (AtGrasp ?a ?o ?g)))
  )

  (:derived (UnsafeBTraj ?t) (or
    (exists (?o2 ?p2) (and (TrajPoseCollision ?t ?o2 ?p2)
                           (AtPose ?o2 ?p2)))
    (exists (?a ?q) (and (TrajArmCollision ?t ?a ?q)
                         (AtAConf ?a ?q)))
    (exists (?a ?o ?g) (and (TrajGraspCollision ?t ?a ?o ?g)
                         (AtGrasp ?a ?o ?g)))
  ))
)