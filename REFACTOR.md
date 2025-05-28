[ ] Rename `Conversation` in openhands/server to `ServerConversation`
[ ] Replace all instances of `sid` in openhands/* to `conversation_id`
[ ] Make EventStream take in a `conversation_id` in its constructor.
    * remove `conversation_id` from all methods on EventStream and use self.conversation_id instead.
    * fix all callers of EventStream to pass in `conversation_id` in the constructor and remove it from the method calls.
[ ] Rename AppConfig to OpenHandsConfig
[ ] Create a new class `Conversation` in openhands/core/ that will be the main interface for conversations.
  * Its constructor will take in a:
      * conversation_id (string)
      * Runtime
      * LLM
      * EventStream
      * AgentController
    * No logic, it's just a dataclass
[ ] Add a new OpenHands class to openhands/core/ which will take care of creating Conversations
  * Constructor is ONLY an OpenHandsConfig
  * Only one method: `create_conversation()`
      * This will create a Runtime, LLM, EventStream, and AgentController, and return a Conversation object.
      * These objects will be created according to the OpenHandsConfig passed in to the constructor.
