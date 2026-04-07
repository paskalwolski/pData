# readme.md


#  Architecture

## Game Layer 
 Purely focused on interactions with the game: 
 - AcStart
 - AcUpdate
 - AcShutdown
 
## Controller Layer
'Threads' that manage different functionalities. Lifecycle contained by Ac functions above. 
- EventController
- TrackDataController
- CarDataController

### EventController
Tracks bare minimum data to do with the specific driver in the event, and manages everything to do with Sessions in the Event.

**Event Data** 
- Things like [Server Name], Track, Driver, Car. Used to build the `SessionData` bundle.
- Does NOT handle detailed Track Data - this remains in the `TrackDataController`. However, we do need to know the track ID for SessionData. 

**Session Management**
- Decides when a Session starts and ends. This MIGHT require some knowledge of laps as well? 
    - AC Session Restart - we remain in the same Session (eg. "Practice"), but the lap counter is reset - this means there's a new session.
    - Maybe enough that `Session` can close itself? Would have to notify its parent to create a new one, then. 
    - Worth it to query the active Session with every update? We can have it return Boolean based on the update, and allow the Controller to create a new Session if False
    - Alternatively, is aware of the `Session` properties, and can make decisions based on that. Probably a better idea to do this...
- No Network requests - simply takes the data bundle from AC, and decides if it goes into the current or a new session

### `TrackDataController`
Manages detailed data to do with the track 

**Track Detail Gathering**  
Fetching and reading detailed track data like: 
1. Neat Track Name
2. Track Map Data
3. Track Section Data

**Network Requests**
1. Fetch available track data, to see what exists on the database - this is useful as it's very useful data, but it's not always reliable on the local
2. Post available track data, to update the DB - send all the available data to be stored. 

**In-Game Track Interface**
- Track Data Uploads are done manually - as the available track data is not always in a good condition. Primary Action button to do this.
- Interface displays the state of the Remote and Local track allowing the user to make an informed upload choice

### `CarDataController`
Manages detailed data to do with the car. 

**Car Detail Gathering**
- Fetching Data relating to the Car:
    1. Car Name (`ui.json`)
    2. That's it...  I think

**Network Request**
- Basic Send Data: Car data is very limited (for now) and will not require care when uploading. 

-------

## Data Controllers
Data controllers are basically:
```
[Fetch Data] - - - \
Read File Data - - + - > [Confirm Upload] - - - > Upload Data
```

- In order to manage the reads, that should also be threaded. 
- TrackDataController requires complex updating: When read finished, when fetch finished, when send finished. 
- CarDataController is pretty much sequential: gather -> send -> success. 

-------

## Lifecycle Classes

### `Session`
Leeps track of what's going on in the current session, and can be closed at the end of a session. 

- Init'ed with `EventData`
- Tracks things like current lap (or session laps), best lap reference, as well as `EventData`
    - Potentially also `lapStartMeters` - to account for laps where the finish line is not at 0m
- Manages Laps
    1. Receives a telemetry bundle from EventController
    2. Decides if it's relevant for the current lap, or no
    3. Creates and destroys laps as required
- On close, registers the final session data so that we can track available lap count
    - Only does so if we have valid laps! Otherwise, this session is empty. 

### `Lap`
Bundles all telemetry relating to a single lap and sends the lap data. 

- Init'ed with `SessionData` - so that it knows which session it belongs to - lap number
    - No 'total lap count' though - Lap is only aware of its own lap number
- Receives telemtry bundle from `Session` and tracks it
- On close, it POSTs all lap telemtry to the `handleLap` endpoint

------ 

## Realtime Functionality Expansions
Expansion options that would use Firestore Realtime Database - no idea if this is available or not. 
1. Event Enrolment - rather than having Sessions as the top-level data structure, we could have events. 
    - Drivers would 'enrol' in an event, making the realtime DB aware of their connection
    - All sessions during an enrolment would be tagged under the event - even if they come from different drivers
        - Potentially extended to a Session enrollment as well