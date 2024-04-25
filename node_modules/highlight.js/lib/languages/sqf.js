/*
Language: SQF
Author: Søren Enevoldsen <senevoldsen90@gmail.com>
Contributors: Marvin Saignat <contact@zgmrvn.com>, Dedmen Miller <dedmen@dedmen.de>
Description: Scripting language for the Arma game series
Website: https://community.bistudio.com/wiki/SQF_syntax
Category: scripting
*/

function sqf(hljs) {
  // In SQF, a variable start with _
  const VARIABLE = {
    className: 'variable',
    begin: /\b_+[a-zA-Z]\w*/
  };

  // In SQF, a function should fit myTag_fnc_myFunction pattern
  // https://community.bistudio.com/wiki/Functions_Library_(Arma_3)#Adding_a_Function
  const FUNCTION = {
    className: 'title',
    begin: /[a-zA-Z][a-zA-Z0-9]+_fnc_\w*/
  };

  // In SQF strings, quotes matching the start are escaped by adding a consecutive.
  // Example of single escaped quotes: " "" " and  ' '' '.
  const STRINGS = {
    className: 'string',
    variants: [
      {
        begin: '"',
        end: '"',
        contains: [ {
          begin: '""',
          relevance: 0
        } ]
      },
      {
        begin: '\'',
        end: '\'',
        contains: [ {
          begin: '\'\'',
          relevance: 0
        } ]
      }
    ]
  };

  // list of keywords from:
  // https://community.bistudio.com/wiki/PreProcessor_Commands
  const PREPROCESSOR = {
    className: 'meta',
    begin: /#\s*[a-z]+\b/,
    end: /$/,
    keywords: {
      'meta-keyword':
        'define undef ifdef ifndef else endif include'
    },
    contains: [
      {
        begin: /\\\n/,
        relevance: 0
      },
      hljs.inherit(STRINGS, {
        className: 'meta-string'
      }),
      {
        className: 'meta-string',
        begin: /<[^\n>]*>/,
        end: /$/,
        illegal: '\\n'
      },
      hljs.C_LINE_COMMENT_MODE,
      hljs.C_BLOCK_COMMENT_MODE
    ]
  };

  return {
    name: 'SQF',
    case_insensitive: true,
    keywords: {
      keyword:
        'case catch default do else exit exitWith for forEach from if ' +
        'private switch then throw to try waitUntil while with',
      built_in:
        'abs accTime acos action actionIDs actionKeys actionKeysImages actionKeysNames ' +
        'actionKeysNamesArray actionName actionParams activateAddons activatedAddons activateKey ' +
        'add3DENConnection add3DENEventHandler add3DENLayer addAction addBackpack addBackpackCargo ' +
        'addBackpackCargoGlobal addBackpackGlobal addCamShake addCuratorAddons addCuratorCameraArea ' +
        'addCuratorEditableObjects addCuratorEditingArea addCuratorPoints addEditorObject addEventHandler ' +
        'addForce addGoggles addGroupIcon addHandgunItem addHeadgear addItem addItemCargo ' +
        'addItemCargoGlobal addItemPool addItemToBackpack addItemToUniform addItemToVest addLiveStats ' +
        'addMagazine addMagazineAmmoCargo addMagazineCargo addMagazineCargoGlobal addMagazineGlobal ' +
        'addMagazinePool addMagazines addMagazineTurret addMenu addMenuItem addMissionEventHandler ' +
        'addMPEventHandler addMusicEventHandler addOwnedMine addPlayerScores addPrimaryWeaponItem ' +
        'addPublicVariableEventHandler addRating addResources addScore addScoreSide addSecondaryWeaponItem ' +
        'addSwitchableUnit addTeamMember addToRemainsCollector addTorque addUniform addVehicle addVest ' +
        'addWaypoint addWeapon addWeaponCargo addWeaponCargoGlobal addWeaponGlobal addWeaponItem ' +
        'addWeaponPool addWeaponTurret admin agent agents AGLToASL aimedAtTarget aimPos airDensityRTD ' +
        'airplaneThrottle airportSide AISFinishHeal alive all3DENEntities allAirports allControls ' +
        'allCurators allCutLayers allDead allDeadMen allDisplays allGroups allMapMarkers allMines ' +
        'allMissionObjects allow3DMode allowCrewInImmobile allowCuratorLogicIgnoreAreas allowDamage ' +
        'allowDammage allowFileOperations allowFleeing allowGetIn allowSprint allPlayers allSimpleObjects ' +
        'allSites allTurrets allUnits allUnitsUAV allVariables ammo ammoOnPylon and animate animateBay ' +
        'animateDoor animatePylon animateSource animationNames animationPhase animationSourcePhase ' +
        'animationState append apply armoryPoints arrayIntersect asin ASLToAGL ASLToATL assert ' +
        'assignAsCargo assignAsCargoIndex assignAsCommander assignAsDriver assignAsGunner assignAsTurret ' +
        'assignCurator assignedCargo assignedCommander assignedDriver assignedGunner assignedItems ' +
        'assignedTarget assignedTeam assignedVehicle assignedVehicleRole assignItem assignTeam ' +
        'assignToAirport atan atan2 atg ATLToASL attachedObject attachedObjects attachedTo attachObject ' +
        'attachTo attackEnabled backpack backpackCargo backpackContainer backpackItems backpackMagazines ' +
        'backpackSpaceFor behaviour benchmark binocular boundingBox boundingBoxReal boundingCenter ' +
        'breakOut breakTo briefingName buildingExit buildingPos buttonAction buttonSetAction cadetMode ' +
        'call callExtension camCommand camCommit camCommitPrepared camCommitted camConstuctionSetParams ' +
        'camCreate camDestroy cameraEffect cameraEffectEnableHUD cameraInterest cameraOn cameraView ' +
        'campaignConfigFile camPreload camPreloaded camPrepareBank camPrepareDir camPrepareDive ' +
        'camPrepareFocus camPrepareFov camPrepareFovRange camPreparePos camPrepareRelPos camPrepareTarget ' +
        'camSetBank camSetDir camSetDive camSetFocus camSetFov camSetFovRange camSetPos camSetRelPos ' +
        'camSetTarget camTarget camUseNVG canAdd canAddItemToBackpack canAddItemToUniform canAddItemToVest ' +
        'cancelSimpleTaskDestination canFire canMove canSlingLoad canStand canSuspend ' +
        'canTriggerDynamicSimulation canUnloadInCombat canVehicleCargo captive captiveNum cbChecked ' +
        'cbSetChecked ceil channelEnabled cheatsEnabled checkAIFeature checkVisibility className ' +
        'clearAllItemsFromBackpack clearBackpackCargo clearBackpackCargoGlobal clearGroupIcons ' +
        'clearItemCargo clearItemCargoGlobal clearItemPool clearMagazineCargo clearMagazineCargoGlobal ' +
        'clearMagazinePool clearOverlay clearRadio clearWeaponCargo clearWeaponCargoGlobal clearWeaponPool ' +
        'clientOwner closeDialog closeDisplay closeOverlay collapseObjectTree collect3DENHistory ' +
        'collectiveRTD combatMode commandArtilleryFire commandChat commander commandFire commandFollow ' +
        'commandFSM commandGetOut commandingMenu commandMove commandRadio commandStop ' +
        'commandSuppressiveFire commandTarget commandWatch comment commitOverlay compile compileFinal ' +
        'completedFSM composeText configClasses configFile configHierarchy configName configProperties ' +
        'configSourceAddonList configSourceMod configSourceModList confirmSensorTarget ' +
        'connectTerminalToUAV controlsGroupCtrl copyFromClipboard copyToClipboard copyWaypoints cos count ' +
        'countEnemy countFriendly countSide countType countUnknown create3DENComposition create3DENEntity ' +
        'createAgent createCenter createDialog createDiaryLink createDiaryRecord createDiarySubject ' +
        'createDisplay createGearDialog createGroup createGuardedPoint createLocation createMarker ' +
        'createMarkerLocal createMenu createMine createMissionDisplay createMPCampaignDisplay ' +
        'createSimpleObject createSimpleTask createSite createSoundSource createTask createTeam ' +
        'createTrigger createUnit createVehicle createVehicleCrew createVehicleLocal crew ctAddHeader ' +
        'ctAddRow ctClear ctCurSel ctData ctFindHeaderRows ctFindRowHeader ctHeaderControls ctHeaderCount ' +
        'ctRemoveHeaders ctRemoveRows ctrlActivate ctrlAddEventHandler ctrlAngle ctrlAutoScrollDelay ' +
        'ctrlAutoScrollRewind ctrlAutoScrollSpeed ctrlChecked ctrlClassName ctrlCommit ctrlCommitted ' +
        'ctrlCreate ctrlDelete ctrlEnable ctrlEnabled ctrlFade ctrlHTMLLoaded ctrlIDC ctrlIDD ' +
        'ctrlMapAnimAdd ctrlMapAnimClear ctrlMapAnimCommit ctrlMapAnimDone ctrlMapCursor ctrlMapMouseOver ' +
        'ctrlMapScale ctrlMapScreenToWorld ctrlMapWorldToScreen ctrlModel ctrlModelDirAndUp ctrlModelScale ' +
        'ctrlParent ctrlParentControlsGroup ctrlPosition ctrlRemoveAllEventHandlers ctrlRemoveEventHandler ' +
        'ctrlScale ctrlSetActiveColor ctrlSetAngle ctrlSetAutoScrollDelay ctrlSetAutoScrollRewind ' +
        'ctrlSetAutoScrollSpeed ctrlSetBackgroundColor ctrlSetChecked ctrlSetEventHandler ctrlSetFade ' +
        'ctrlSetFocus ctrlSetFont ctrlSetFontH1 ctrlSetFontH1B ctrlSetFontH2 ctrlSetFontH2B ctrlSetFontH3 ' +
        'ctrlSetFontH3B ctrlSetFontH4 ctrlSetFontH4B ctrlSetFontH5 ctrlSetFontH5B ctrlSetFontH6 ' +
        'ctrlSetFontH6B ctrlSetFontHeight ctrlSetFontHeightH1 ctrlSetFontHeightH2 ctrlSetFontHeightH3 ' +
        'ctrlSetFontHeightH4 ctrlSetFontHeightH5 ctrlSetFontHeightH6 ctrlSetFontHeightSecondary ' +
        'ctrlSetFontP ctrlSetFontPB ctrlSetFontSecondary ctrlSetForegroundColor ctrlSetModel ' +
        'ctrlSetModelDirAndUp ctrlSetModelScale ctrlSetPixelPrecision ctrlSetPosition ctrlSetScale ' +
        'ctrlSetStructuredText ctrlSetText ctrlSetTextColor ctrlSetTooltip ctrlSetTooltipColorBox ' +
        'ctrlSetTooltipColorShade ctrlSetTooltipColorText ctrlShow ctrlShown ctrlText ctrlTextHeight ' +
        'ctrlTextWidth ctrlType ctrlVisible ctRowControls ctRowCount ctSetCurSel ctSetData ' +
        'ctSetHeaderTemplate ctSetRowTemplate ctSetValue ctValue curatorAddons curatorCamera ' +
        'curatorCameraArea curatorCameraAreaCeiling curatorCoef curatorEditableObjects curatorEditingArea ' +
        'curatorEditingAreaType curatorMouseOver curatorPoints curatorRegisteredObjects curatorSelected ' +
        'curatorWaypointCost current3DENOperation currentChannel currentCommand currentMagazine ' +
        'currentMagazineDetail currentMagazineDetailTurret currentMagazineTurret currentMuzzle ' +
        'currentNamespace currentTask currentTasks currentThrowable currentVisionMode currentWaypoint ' +
        'currentWeapon currentWeaponMode currentWeaponTurret currentZeroing cursorObject cursorTarget ' +
        'customChat customRadio cutFadeOut cutObj cutRsc cutText damage date dateToNumber daytime ' +
        'deActivateKey debriefingText debugFSM debugLog deg delete3DENEntities deleteAt deleteCenter ' +
        'deleteCollection deleteEditorObject deleteGroup deleteGroupWhenEmpty deleteIdentity ' +
        'deleteLocation deleteMarker deleteMarkerLocal deleteRange deleteResources deleteSite deleteStatus ' +
        'deleteTeam deleteVehicle deleteVehicleCrew deleteWaypoint detach detectedMines ' +
        'diag_activeMissionFSMs diag_activeScripts diag_activeSQFScripts diag_activeSQSScripts ' +
        'diag_captureFrame diag_captureFrameToFile diag_captureSlowFrame diag_codePerformance ' +
        'diag_drawMode diag_enable diag_enabled diag_fps diag_fpsMin diag_frameNo diag_lightNewLoad ' +
        'diag_list diag_log diag_logSlowFrame diag_mergeConfigFile diag_recordTurretLimits ' +
        'diag_setLightNew diag_tickTime diag_toggle dialog diarySubjectExists didJIP didJIPOwner ' +
        'difficulty difficultyEnabled difficultyEnabledRTD difficultyOption direction directSay disableAI ' +
        'disableCollisionWith disableConversation disableDebriefingStats disableMapIndicators ' +
        'disableNVGEquipment disableRemoteSensors disableSerialization disableTIEquipment ' +
        'disableUAVConnectability disableUserInput displayAddEventHandler displayCtrl displayParent ' +
        'displayRemoveAllEventHandlers displayRemoveEventHandler displaySetEventHandler dissolveTeam ' +
        'distance distance2D distanceSqr distributionRegion do3DENAction doArtilleryFire doFire doFollow ' +
        'doFSM doGetOut doMove doorPhase doStop doSuppressiveFire doTarget doWatch drawArrow drawEllipse ' +
        'drawIcon drawIcon3D drawLine drawLine3D drawLink drawLocation drawPolygon drawRectangle ' +
        'drawTriangle driver drop dynamicSimulationDistance dynamicSimulationDistanceCoef ' +
        'dynamicSimulationEnabled dynamicSimulationSystemEnabled echo edit3DENMissionAttributes editObject ' +
        'editorSetEventHandler effectiveCommander emptyPositions enableAI enableAIFeature ' +
        'enableAimPrecision enableAttack enableAudioFeature enableAutoStartUpRTD enableAutoTrimRTD ' +
        'enableCamShake enableCaustics enableChannel enableCollisionWith enableCopilot ' +
        'enableDebriefingStats enableDiagLegend enableDynamicSimulation enableDynamicSimulationSystem ' +
        'enableEndDialog enableEngineArtillery enableEnvironment enableFatigue enableGunLights ' +
        'enableInfoPanelComponent enableIRLasers enableMimics enablePersonTurret enableRadio enableReload ' +
        'enableRopeAttach enableSatNormalOnDetail enableSaving enableSentences enableSimulation ' +
        'enableSimulationGlobal enableStamina enableTeamSwitch enableTraffic enableUAVConnectability ' +
        'enableUAVWaypoints enableVehicleCargo enableVehicleSensor enableWeaponDisassembly ' +
        'endLoadingScreen endMission engineOn enginesIsOnRTD enginesRpmRTD enginesTorqueRTD entities ' +
        'environmentEnabled estimatedEndServerTime estimatedTimeLeft evalObjectArgument everyBackpack ' +
        'everyContainer exec execEditorScript execFSM execVM exp expectedDestination exportJIPMessages ' +
        'eyeDirection eyePos face faction fadeMusic fadeRadio fadeSound fadeSpeech failMission ' +
        'fillWeaponsFromPool find findCover findDisplay findEditorObject findEmptyPosition ' +
        'findEmptyPositionReady findIf findNearestEnemy finishMissionInit finite fire fireAtTarget ' +
        'firstBackpack flag flagAnimationPhase flagOwner flagSide flagTexture fleeing floor flyInHeight ' +
        'flyInHeightASL fog fogForecast fogParams forceAddUniform forcedMap forceEnd forceFlagTexture ' +
        'forceFollowRoad forceMap forceRespawn forceSpeed forceWalk forceWeaponFire forceWeatherChange ' +
        'forEachMember forEachMemberAgent forEachMemberTeam forgetTarget format formation ' +
        'formationDirection formationLeader formationMembers formationPosition formationTask formatText ' +
        'formLeader freeLook fromEditor fuel fullCrew gearIDCAmmoCount gearSlotAmmoCount gearSlotData ' +
        'get3DENActionState get3DENAttribute get3DENCamera get3DENConnections get3DENEntity ' +
        'get3DENEntityID get3DENGrid get3DENIconsVisible get3DENLayerEntities get3DENLinesVisible ' +
        'get3DENMissionAttribute get3DENMouseOver get3DENSelected getAimingCoef getAllEnvSoundControllers ' +
        'getAllHitPointsDamage getAllOwnedMines getAllSoundControllers getAmmoCargo getAnimAimPrecision ' +
        'getAnimSpeedCoef getArray getArtilleryAmmo getArtilleryComputerSettings getArtilleryETA ' +
        'getAssignedCuratorLogic getAssignedCuratorUnit getBackpackCargo getBleedingRemaining ' +
        'getBurningValue getCameraViewDirection getCargoIndex getCenterOfMass getClientState ' +
        'getClientStateNumber getCompatiblePylonMagazines getConnectedUAV getContainerMaxLoad ' +
        'getCursorObjectParams getCustomAimCoef getDammage getDescription getDir getDirVisual ' +
        'getDLCAssetsUsage getDLCAssetsUsageByName getDLCs getEditorCamera getEditorMode ' +
        'getEditorObjectScope getElevationOffset getEnvSoundController getFatigue getForcedFlagTexture ' +
        'getFriend getFSMVariable getFuelCargo getGroupIcon getGroupIconParams getGroupIcons getHideFrom ' +
        'getHit getHitIndex getHitPointDamage getItemCargo getMagazineCargo getMarkerColor getMarkerPos ' +
        'getMarkerSize getMarkerType getMass getMissionConfig getMissionConfigValue getMissionDLCs ' +
        'getMissionLayerEntities getModelInfo getMousePosition getMusicPlayedTime getNumber ' +
        'getObjectArgument getObjectChildren getObjectDLC getObjectMaterials getObjectProxy ' +
        'getObjectTextures getObjectType getObjectViewDistance getOxygenRemaining getPersonUsedDLCs ' +
        'getPilotCameraDirection getPilotCameraPosition getPilotCameraRotation getPilotCameraTarget ' +
        'getPlateNumber getPlayerChannel getPlayerScores getPlayerUID getPos getPosASL getPosASLVisual ' +
        'getPosASLW getPosATL getPosATLVisual getPosVisual getPosWorld getPylonMagazines getRelDir ' +
        'getRelPos getRemoteSensorsDisabled getRepairCargo getResolution getShadowDistance getShotParents ' +
        'getSlingLoad getSoundController getSoundControllerResult getSpeed getStamina getStatValue ' +
        'getSuppression getTerrainGrid getTerrainHeightASL getText getTotalDLCUsageTime getUnitLoadout ' +
        'getUnitTrait getUserMFDText getUserMFDvalue getVariable getVehicleCargo getWeaponCargo ' +
        'getWeaponSway getWingsOrientationRTD getWingsPositionRTD getWPPos glanceAt globalChat globalRadio ' +
        'goggles goto group groupChat groupFromNetId groupIconSelectable groupIconsVisible groupId ' +
        'groupOwner groupRadio groupSelectedUnits groupSelectUnit gunner gusts halt handgunItems ' +
        'handgunMagazine handgunWeapon handsHit hasInterface hasPilotCamera hasWeapon hcAllGroups ' +
        'hcGroupParams hcLeader hcRemoveAllGroups hcRemoveGroup hcSelected hcSelectGroup hcSetGroup ' +
        'hcShowBar hcShownBar headgear hideBody hideObject hideObjectGlobal hideSelection hint hintC ' +
        'hintCadet hintSilent hmd hostMission htmlLoad HUDMovementLevels humidity image importAllGroups ' +
        'importance in inArea inAreaArray incapacitatedState inflame inflamed infoPanel ' +
        'infoPanelComponentEnabled infoPanelComponents infoPanels inGameUISetEventHandler inheritsFrom ' +
        'initAmbientLife inPolygon inputAction inRangeOfArtillery insertEditorObject intersect is3DEN ' +
        'is3DENMultiplayer isAbleToBreathe isAgent isArray isAutoHoverOn isAutonomous isAutotest ' +
        'isBleeding isBurning isClass isCollisionLightOn isCopilotEnabled isDamageAllowed isDedicated ' +
        'isDLCAvailable isEngineOn isEqualTo isEqualType isEqualTypeAll isEqualTypeAny isEqualTypeArray ' +
        'isEqualTypeParams isFilePatchingEnabled isFlashlightOn isFlatEmpty isForcedWalk isFormationLeader ' +
        'isGroupDeletedWhenEmpty isHidden isInRemainsCollector isInstructorFigureEnabled isIRLaserOn ' +
        'isKeyActive isKindOf isLaserOn isLightOn isLocalized isManualFire isMarkedForCollection ' +
        'isMultiplayer isMultiplayerSolo isNil isNull isNumber isObjectHidden isObjectRTD isOnRoad ' +
        'isPipEnabled isPlayer isRealTime isRemoteExecuted isRemoteExecutedJIP isServer isShowing3DIcons ' +
        'isSimpleObject isSprintAllowed isStaminaEnabled isSteamMission isStreamFriendlyUIEnabled isText ' +
        'isTouchingGround isTurnedOut isTutHintsEnabled isUAVConnectable isUAVConnected isUIContext ' +
        'isUniformAllowed isVehicleCargo isVehicleRadarOn isVehicleSensorEnabled isWalking ' +
        'isWeaponDeployed isWeaponRested itemCargo items itemsWithMagazines join joinAs joinAsSilent ' +
        'joinSilent joinString kbAddDatabase kbAddDatabaseTargets kbAddTopic kbHasTopic kbReact ' +
        'kbRemoveTopic kbTell kbWasSaid keyImage keyName knowsAbout land landAt landResult language ' +
        'laserTarget lbAdd lbClear lbColor lbColorRight lbCurSel lbData lbDelete lbIsSelected lbPicture ' +
        'lbPictureRight lbSelection lbSetColor lbSetColorRight lbSetCurSel lbSetData lbSetPicture ' +
        'lbSetPictureColor lbSetPictureColorDisabled lbSetPictureColorSelected lbSetPictureRight ' +
        'lbSetPictureRightColor lbSetPictureRightColorDisabled lbSetPictureRightColorSelected ' +
        'lbSetSelectColor lbSetSelectColorRight lbSetSelected lbSetText lbSetTextRight lbSetTooltip ' +
        'lbSetValue lbSize lbSort lbSortByValue lbText lbTextRight lbValue leader leaderboardDeInit ' +
        'leaderboardGetRows leaderboardInit leaderboardRequestRowsFriends leaderboardsRequestUploadScore ' +
        'leaderboardsRequestUploadScoreKeepBest leaderboardState leaveVehicle libraryCredits ' +
        'libraryDisclaimers lifeState lightAttachObject lightDetachObject lightIsOn lightnings limitSpeed ' +
        'linearConversion lineIntersects lineIntersectsObjs lineIntersectsSurfaces lineIntersectsWith ' +
        'linkItem list listObjects listRemoteTargets listVehicleSensors ln lnbAddArray lnbAddColumn ' +
        'lnbAddRow lnbClear lnbColor lnbCurSelRow lnbData lnbDeleteColumn lnbDeleteRow ' +
        'lnbGetColumnsPosition lnbPicture lnbSetColor lnbSetColumnsPos lnbSetCurSelRow lnbSetData ' +
        'lnbSetPicture lnbSetText lnbSetValue lnbSize lnbSort lnbSortByValue lnbText lnbValue load loadAbs ' +
        'loadBackpack loadFile loadGame loadIdentity loadMagazine loadOverlay loadStatus loadUniform ' +
        'loadVest local localize locationPosition lock lockCameraTo lockCargo lockDriver locked ' +
        'lockedCargo lockedDriver lockedTurret lockIdentity lockTurret lockWP log logEntities logNetwork ' +
        'logNetworkTerminate lookAt lookAtPos magazineCargo magazines magazinesAllTurrets magazinesAmmo ' +
        'magazinesAmmoCargo magazinesAmmoFull magazinesDetail magazinesDetailBackpack ' +
        'magazinesDetailUniform magazinesDetailVest magazinesTurret magazineTurretAmmo mapAnimAdd ' +
        'mapAnimClear mapAnimCommit mapAnimDone mapCenterOnCamera mapGridPosition markAsFinishedOnSteam ' +
        'markerAlpha markerBrush markerColor markerDir markerPos markerShape markerSize markerText ' +
        'markerType max members menuAction menuAdd menuChecked menuClear menuCollapse menuData menuDelete ' +
        'menuEnable menuEnabled menuExpand menuHover menuPicture menuSetAction menuSetCheck menuSetData ' +
        'menuSetPicture menuSetValue menuShortcut menuShortcutText menuSize menuSort menuText menuURL ' +
        'menuValue min mineActive mineDetectedBy missionConfigFile missionDifficulty missionName ' +
        'missionNamespace missionStart missionVersion mod modelToWorld modelToWorldVisual ' +
        'modelToWorldVisualWorld modelToWorldWorld modParams moonIntensity moonPhase morale move ' +
        'move3DENCamera moveInAny moveInCargo moveInCommander moveInDriver moveInGunner moveInTurret ' +
        'moveObjectToEnd moveOut moveTime moveTo moveToCompleted moveToFailed musicVolume name nameSound ' +
        'nearEntities nearestBuilding nearestLocation nearestLocations nearestLocationWithDubbing ' +
        'nearestObject nearestObjects nearestTerrainObjects nearObjects nearObjectsReady nearRoads ' +
        'nearSupplies nearTargets needReload netId netObjNull newOverlay nextMenuItemIndex ' +
        'nextWeatherChange nMenuItems not numberOfEnginesRTD numberToDate objectCurators objectFromNetId ' +
        'objectParent objStatus onBriefingGroup onBriefingNotes onBriefingPlan onBriefingTeamSwitch ' +
        'onCommandModeChanged onDoubleClick onEachFrame onGroupIconClick onGroupIconOverEnter ' +
        'onGroupIconOverLeave onHCGroupSelectionChanged onMapSingleClick onPlayerConnected ' +
        'onPlayerDisconnected onPreloadFinished onPreloadStarted onShowNewObject onTeamSwitch ' +
        'openCuratorInterface openDLCPage openMap openSteamApp openYoutubeVideo or orderGetIn overcast ' +
        'overcastForecast owner param params parseNumber parseSimpleArray parseText parsingNamespace ' +
        'particlesQuality pickWeaponPool pitch pixelGrid pixelGridBase pixelGridNoUIScale pixelH pixelW ' +
        'playableSlotsNumber playableUnits playAction playActionNow player playerRespawnTime playerSide ' +
        'playersNumber playGesture playMission playMove playMoveNow playMusic playScriptedMission ' +
        'playSound playSound3D position positionCameraToWorld posScreenToWorld posWorldToScreen ' +
        'ppEffectAdjust ppEffectCommit ppEffectCommitted ppEffectCreate ppEffectDestroy ppEffectEnable ' +
        'ppEffectEnabled ppEffectForceInNVG precision preloadCamera preloadObject preloadSound ' +
        'preloadTitleObj preloadTitleRsc preprocessFile preprocessFileLineNumbers primaryWeapon ' +
        'primaryWeaponItems primaryWeaponMagazine priority processDiaryLink productVersion profileName ' +
        'profileNamespace profileNameSteam progressLoadingScreen progressPosition progressSetPosition ' +
        'publicVariable publicVariableClient publicVariableServer pushBack pushBackUnique putWeaponPool ' +
        'queryItemsPool queryMagazinePool queryWeaponPool rad radioChannelAdd radioChannelCreate ' +
        'radioChannelRemove radioChannelSetCallSign radioChannelSetLabel radioVolume rain rainbow random ' +
        'rank rankId rating rectangular registeredTasks registerTask reload reloadEnabled remoteControl ' +
        'remoteExec remoteExecCall remoteExecutedOwner remove3DENConnection remove3DENEventHandler ' +
        'remove3DENLayer removeAction removeAll3DENEventHandlers removeAllActions removeAllAssignedItems ' +
        'removeAllContainers removeAllCuratorAddons removeAllCuratorCameraAreas ' +
        'removeAllCuratorEditingAreas removeAllEventHandlers removeAllHandgunItems removeAllItems ' +
        'removeAllItemsWithMagazines removeAllMissionEventHandlers removeAllMPEventHandlers ' +
        'removeAllMusicEventHandlers removeAllOwnedMines removeAllPrimaryWeaponItems removeAllWeapons ' +
        'removeBackpack removeBackpackGlobal removeCuratorAddons removeCuratorCameraArea ' +
        'removeCuratorEditableObjects removeCuratorEditingArea removeDrawIcon removeDrawLinks ' +
        'removeEventHandler removeFromRemainsCollector removeGoggles removeGroupIcon removeHandgunItem ' +
        'removeHeadgear removeItem removeItemFromBackpack removeItemFromUniform removeItemFromVest ' +
        'removeItems removeMagazine removeMagazineGlobal removeMagazines removeMagazinesTurret ' +
        'removeMagazineTurret removeMenuItem removeMissionEventHandler removeMPEventHandler ' +
        'removeMusicEventHandler removeOwnedMine removePrimaryWeaponItem removeSecondaryWeaponItem ' +
        'removeSimpleTask removeSwitchableUnit removeTeamMember removeUniform removeVest removeWeapon ' +
        'removeWeaponAttachmentCargo removeWeaponCargo removeWeaponGlobal removeWeaponTurret ' +
        'reportRemoteTarget requiredVersion resetCamShake resetSubgroupDirection resize resources ' +
        'respawnVehicle restartEditorCamera reveal revealMine reverse reversedMouseY roadAt ' +
        'roadsConnectedTo roleDescription ropeAttachedObjects ropeAttachedTo ropeAttachEnabled ' +
        'ropeAttachTo ropeCreate ropeCut ropeDestroy ropeDetach ropeEndPosition ropeLength ropes ' +
        'ropeUnwind ropeUnwound rotorsForcesRTD rotorsRpmRTD round runInitScript safeZoneH safeZoneW ' +
        'safeZoneWAbs safeZoneX safeZoneXAbs safeZoneY save3DENInventory saveGame saveIdentity ' +
        'saveJoysticks saveOverlay saveProfileNamespace saveStatus saveVar savingEnabled say say2D say3D ' +
        'scopeName score scoreSide screenshot screenToWorld scriptDone scriptName scudState ' +
        'secondaryWeapon secondaryWeaponItems secondaryWeaponMagazine select selectBestPlaces ' +
        'selectDiarySubject selectedEditorObjects selectEditorObject selectionNames selectionPosition ' +
        'selectLeader selectMax selectMin selectNoPlayer selectPlayer selectRandom selectRandomWeighted ' +
        'selectWeapon selectWeaponTurret sendAUMessage sendSimpleCommand sendTask sendTaskResult ' +
        'sendUDPMessage serverCommand serverCommandAvailable serverCommandExecutable serverName serverTime ' +
        'set set3DENAttribute set3DENAttributes set3DENGrid set3DENIconsVisible set3DENLayer ' +
        'set3DENLinesVisible set3DENLogicType set3DENMissionAttribute set3DENMissionAttributes ' +
        'set3DENModelsVisible set3DENObjectType set3DENSelected setAccTime setActualCollectiveRTD ' +
        'setAirplaneThrottle setAirportSide setAmmo setAmmoCargo setAmmoOnPylon setAnimSpeedCoef ' +
        'setAperture setApertureNew setArmoryPoints setAttributes setAutonomous setBehaviour ' +
        'setBleedingRemaining setBrakesRTD setCameraInterest setCamShakeDefParams setCamShakeParams ' +
        'setCamUseTI setCaptive setCenterOfMass setCollisionLight setCombatMode setCompassOscillation ' +
        'setConvoySeparation setCuratorCameraAreaCeiling setCuratorCoef setCuratorEditingAreaType ' +
        'setCuratorWaypointCost setCurrentChannel setCurrentTask setCurrentWaypoint setCustomAimCoef ' +
        'setCustomWeightRTD setDamage setDammage setDate setDebriefingText setDefaultCamera setDestination ' +
        'setDetailMapBlendPars setDir setDirection setDrawIcon setDriveOnPath setDropInterval ' +
        'setDynamicSimulationDistance setDynamicSimulationDistanceCoef setEditorMode setEditorObjectScope ' +
        'setEffectCondition setEngineRPMRTD setFace setFaceAnimation setFatigue setFeatureType ' +
        'setFlagAnimationPhase setFlagOwner setFlagSide setFlagTexture setFog setFormation ' +
        'setFormationTask setFormDir setFriend setFromEditor setFSMVariable setFuel setFuelCargo ' +
        'setGroupIcon setGroupIconParams setGroupIconsSelectable setGroupIconsVisible setGroupId ' +
        'setGroupIdGlobal setGroupOwner setGusts setHideBehind setHit setHitIndex setHitPointDamage ' +
        'setHorizonParallaxCoef setHUDMovementLevels setIdentity setImportance setInfoPanel setLeader ' +
        'setLightAmbient setLightAttenuation setLightBrightness setLightColor setLightDayLight ' +
        'setLightFlareMaxDistance setLightFlareSize setLightIntensity setLightnings setLightUseFlare ' +
        'setLocalWindParams setMagazineTurretAmmo setMarkerAlpha setMarkerAlphaLocal setMarkerBrush ' +
        'setMarkerBrushLocal setMarkerColor setMarkerColorLocal setMarkerDir setMarkerDirLocal ' +
        'setMarkerPos setMarkerPosLocal setMarkerShape setMarkerShapeLocal setMarkerSize ' +
        'setMarkerSizeLocal setMarkerText setMarkerTextLocal setMarkerType setMarkerTypeLocal setMass ' +
        'setMimic setMousePosition setMusicEffect setMusicEventHandler setName setNameSound ' +
        'setObjectArguments setObjectMaterial setObjectMaterialGlobal setObjectProxy setObjectTexture ' +
        'setObjectTextureGlobal setObjectViewDistance setOvercast setOwner setOxygenRemaining ' +
        'setParticleCircle setParticleClass setParticleFire setParticleParams setParticleRandom ' +
        'setPilotCameraDirection setPilotCameraRotation setPilotCameraTarget setPilotLight setPiPEffect ' +
        'setPitch setPlateNumber setPlayable setPlayerRespawnTime setPos setPosASL setPosASL2 setPosASLW ' +
        'setPosATL setPosition setPosWorld setPylonLoadOut setPylonsPriority setRadioMsg setRain ' +
        'setRainbow setRandomLip setRank setRectangular setRepairCargo setRotorBrakeRTD setShadowDistance ' +
        'setShotParents setSide setSimpleTaskAlwaysVisible setSimpleTaskCustomData ' +
        'setSimpleTaskDescription setSimpleTaskDestination setSimpleTaskTarget setSimpleTaskType ' +
        'setSimulWeatherLayers setSize setSkill setSlingLoad setSoundEffect setSpeaker setSpeech ' +
        'setSpeedMode setStamina setStaminaScheme setStatValue setSuppression setSystemOfUnits ' +
        'setTargetAge setTaskMarkerOffset setTaskResult setTaskState setTerrainGrid setText ' +
        'setTimeMultiplier setTitleEffect setTrafficDensity setTrafficDistance setTrafficGap ' +
        'setTrafficSpeed setTriggerActivation setTriggerArea setTriggerStatements setTriggerText ' +
        'setTriggerTimeout setTriggerType setType setUnconscious setUnitAbility setUnitLoadout setUnitPos ' +
        'setUnitPosWeak setUnitRank setUnitRecoilCoefficient setUnitTrait setUnloadInCombat ' +
        'setUserActionText setUserMFDText setUserMFDvalue setVariable setVectorDir setVectorDirAndUp ' +
        'setVectorUp setVehicleAmmo setVehicleAmmoDef setVehicleArmor setVehicleCargo setVehicleId ' +
        'setVehicleLock setVehiclePosition setVehicleRadar setVehicleReceiveRemoteTargets ' +
        'setVehicleReportOwnPosition setVehicleReportRemoteTargets setVehicleTIPars setVehicleVarName ' +
        'setVelocity setVelocityModelSpace setVelocityTransformation setViewDistance ' +
        'setVisibleIfTreeCollapsed setWantedRPMRTD setWaves setWaypointBehaviour setWaypointCombatMode ' +
        'setWaypointCompletionRadius setWaypointDescription setWaypointForceBehaviour setWaypointFormation ' +
        'setWaypointHousePosition setWaypointLoiterRadius setWaypointLoiterType setWaypointName ' +
        'setWaypointPosition setWaypointScript setWaypointSpeed setWaypointStatements setWaypointTimeout ' +
        'setWaypointType setWaypointVisible setWeaponReloadingTime setWind setWindDir setWindForce ' +
        'setWindStr setWingForceScaleRTD setWPPos show3DIcons showChat showCinemaBorder showCommandingMenu ' +
        'showCompass showCuratorCompass showGPS showHUD showLegend showMap shownArtilleryComputer ' +
        'shownChat shownCompass shownCuratorCompass showNewEditorObject shownGPS shownHUD shownMap ' +
        'shownPad shownRadio shownScoretable shownUAVFeed shownWarrant shownWatch showPad showRadio ' +
        'showScoretable showSubtitles showUAVFeed showWarrant showWatch showWaypoint showWaypoints side ' +
        'sideChat sideEnemy sideFriendly sideRadio simpleTasks simulationEnabled simulCloudDensity ' +
        'simulCloudOcclusion simulInClouds simulWeatherSync sin size sizeOf skill skillFinal skipTime ' +
        'sleep sliderPosition sliderRange sliderSetPosition sliderSetRange sliderSetSpeed sliderSpeed ' +
        'slingLoadAssistantShown soldierMagazines someAmmo sort soundVolume spawn speaker speed speedMode ' +
        'splitString sqrt squadParams stance startLoadingScreen step stop stopEngineRTD stopped str ' +
        'sunOrMoon supportInfo suppressFor surfaceIsWater surfaceNormal surfaceType swimInDepth ' +
        'switchableUnits switchAction switchCamera switchGesture switchLight switchMove ' +
        'synchronizedObjects synchronizedTriggers synchronizedWaypoints synchronizeObjectsAdd ' +
        'synchronizeObjectsRemove synchronizeTrigger synchronizeWaypoint systemChat systemOfUnits tan ' +
        'targetKnowledge targets targetsAggregate targetsQuery taskAlwaysVisible taskChildren ' +
        'taskCompleted taskCustomData taskDescription taskDestination taskHint taskMarkerOffset taskParent ' +
        'taskResult taskState taskType teamMember teamName teams teamSwitch teamSwitchEnabled teamType ' +
        'terminate terrainIntersect terrainIntersectASL terrainIntersectAtASL text textLog textLogFormat ' +
        'tg time timeMultiplier titleCut titleFadeOut titleObj titleRsc titleText toArray toFixed toLower ' +
        'toString toUpper triggerActivated triggerActivation triggerArea triggerAttachedVehicle ' +
        'triggerAttachObject triggerAttachVehicle triggerDynamicSimulation triggerStatements triggerText ' +
        'triggerTimeout triggerTimeoutCurrent triggerType turretLocal turretOwner turretUnit tvAdd tvClear ' +
        'tvCollapse tvCollapseAll tvCount tvCurSel tvData tvDelete tvExpand tvExpandAll tvPicture ' +
        'tvSetColor tvSetCurSel tvSetData tvSetPicture tvSetPictureColor tvSetPictureColorDisabled ' +
        'tvSetPictureColorSelected tvSetPictureRight tvSetPictureRightColor tvSetPictureRightColorDisabled ' +
        'tvSetPictureRightColorSelected tvSetText tvSetTooltip tvSetValue tvSort tvSortByValue tvText ' +
        'tvTooltip tvValue type typeName typeOf UAVControl uiNamespace uiSleep unassignCurator ' +
        'unassignItem unassignTeam unassignVehicle underwater uniform uniformContainer uniformItems ' +
        'uniformMagazines unitAddons unitAimPosition unitAimPositionVisual unitBackpack unitIsUAV unitPos ' +
        'unitReady unitRecoilCoefficient units unitsBelowHeight unlinkItem unlockAchievement ' +
        'unregisterTask updateDrawIcon updateMenuItem updateObjectTree useAISteeringComponent ' +
        'useAudioTimeForMoves userInputDisabled vectorAdd vectorCos vectorCrossProduct vectorDiff ' +
        'vectorDir vectorDirVisual vectorDistance vectorDistanceSqr vectorDotProduct vectorFromTo ' +
        'vectorMagnitude vectorMagnitudeSqr vectorModelToWorld vectorModelToWorldVisual vectorMultiply ' +
        'vectorNormalized vectorUp vectorUpVisual vectorWorldToModel vectorWorldToModelVisual vehicle ' +
        'vehicleCargoEnabled vehicleChat vehicleRadio vehicleReceiveRemoteTargets vehicleReportOwnPosition ' +
        'vehicleReportRemoteTargets vehicles vehicleVarName velocity velocityModelSpace verifySignature ' +
        'vest vestContainer vestItems vestMagazines viewDistance visibleCompass visibleGPS visibleMap ' +
        'visiblePosition visiblePositionASL visibleScoretable visibleWatch waves waypointAttachedObject ' +
        'waypointAttachedVehicle waypointAttachObject waypointAttachVehicle waypointBehaviour ' +
        'waypointCombatMode waypointCompletionRadius waypointDescription waypointForceBehaviour ' +
        'waypointFormation waypointHousePosition waypointLoiterRadius waypointLoiterType waypointName ' +
        'waypointPosition waypoints waypointScript waypointsEnabledUAV waypointShow waypointSpeed ' +
        'waypointStatements waypointTimeout waypointTimeoutCurrent waypointType waypointVisible ' +
        'weaponAccessories weaponAccessoriesCargo weaponCargo weaponDirection weaponInertia weaponLowered ' +
        'weapons weaponsItems weaponsItemsCargo weaponState weaponsTurret weightRTD WFSideText wind ',
      literal:
        'blufor civilian configNull controlNull displayNull east endl false grpNull independent lineBreak ' +
        'locationNull nil objNull opfor pi resistance scriptNull sideAmbientLife sideEmpty sideLogic ' +
        'sideUnknown taskNull teamMemberNull true west'
    },
    contains: [
      hljs.C_LINE_COMMENT_MODE,
      hljs.C_BLOCK_COMMENT_MODE,
      hljs.NUMBER_MODE,
      VARIABLE,
      FUNCTION,
      STRINGS,
      PREPROCESSOR
    ],
    illegal: /#|^\$ /
  };
}

module.exports = sqf;
