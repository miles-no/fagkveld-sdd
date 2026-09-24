# Feature Specification: Todo Lists API

**Feature Branch**: `spor/agent-os`

**Created**: 2026-09-24

**Status**: Draft

**Input**: User description: "Et API for gjøremål (TODO) og lister, bygget fra bunnen av. Et gjøremål har en tittel og en status som sier om det er gjort eller ikke. En liste har et navn. Hvert gjøremål hører hjemme i én liste. Gjennom API-et skal man kunne opprette, hente, endre og slette både gjøremål og lister. Man skal kunne hente gjøremålene som ligger i en bestemt liste, og man skal kunne flytte et gjøremål fra én liste til en annen. Spørringer etter noe som ikke finnes er en normal situasjon, ikke et uhell — API-et svarer fornuftig på dem i stedet for å bryte sammen. Data skal overleve en omstart av applikasjonen."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture todos in a named list (Priority: P1)

A consumer of the API creates a named list, adds todos to it, and reads back
everything the list holds. This is the smallest slice that delivers value: a
place to put work and a way to see it again later, including after the service
has been restarted.

**Why this priority**: Nothing else in the feature is usable without it. A todo
cannot exist outside a list, so list creation plus todo creation plus reading
is the minimum viable product.

**Independent Test**: Create a list, add two todos to it, request the list's
todos, and confirm both come back with the titles given and an unfinished
status. Restart the service and repeat the read.

**Acceptance Scenarios**:

1. **Given** no lists exist, **When** a list named "Handleliste" is created,
   **Then** the list is returned with an identifier and that name.
2. **Given** a list exists, **When** a todo titled "Kjøpe melk" is created in
   it, **Then** the todo is returned with that title, an unfinished status, and
   a reference to the list it belongs to.
3. **Given** a list holds two todos, **When** the list's todos are requested,
   **Then** exactly those two todos are returned and no todo from another list.
4. **Given** todos and lists were created earlier, **When** the service is
   stopped and started again, **Then** the same lists and todos are still
   readable with unchanged content.

---

### User Story 2 - Predictable answers for things that do not exist (Priority: P1)

A consumer asks for, changes, or deletes something by an identifier that does
not exist — a deleted list, a mistyped todo identifier, a todo requested inside
the wrong list. The API answers clearly that the thing was not found and keeps
serving other requests normally.

**Why this priority**: It applies to every operation from the first one built,
and it is the behaviour the brief calls out by name. Retrofitting it later means
revisiting every path.

**Independent Test**: For each operation, issue it against an identifier known
not to exist and confirm a clear not-found answer carrying a message that names
what was missing, with no crash and no unhandled failure. Then issue a valid
request and confirm the service still responds.

**Acceptance Scenarios**:

1. **Given** no list has identifier X, **When** the list X is requested,
   **Then** a not-found answer is returned naming the list as missing.
2. **Given** no list has identifier X, **When** a todo is created in list X,
   **Then** a not-found answer is returned and no todo is stored.
3. **Given** a todo exists in list A, **When** it is requested as a todo of
   list B, **Then** a not-found answer is returned rather than the todo.
4. **Given** a not-found answer was just returned, **When** a valid request is
   made, **Then** it succeeds normally.

---

### User Story 3 - Track and revise work (Priority: P2)

A consumer marks a todo as done or not done again, corrects its title, renames
a list, and removes todos or lists that are no longer wanted.

**Why this priority**: Capturing work has standalone value, but the todos are
only useful over time if their status and wording can change and stale entries
can be removed.

**Independent Test**: Create a todo, mark it done, read it back and confirm the
status changed; rename it and confirm the new title; delete it and confirm it
is gone from its list.

**Acceptance Scenarios**:

1. **Given** an unfinished todo, **When** its status is set to done, **Then**
   later reads show it as done and its title is unchanged.
2. **Given** a done todo, **When** its status is set back to not done, **Then**
   later reads show it as unfinished.
3. **Given** a todo, **When** only its title is changed, **Then** its status and
   list membership are unchanged.
4. **Given** a list, **When** its name is changed, **Then** later reads show the
   new name and the list still holds the same todos.
5. **Given** a todo in a list, **When** the todo is deleted, **Then** it is
   absent from the list's todos and requesting it directly gives a not-found
   answer.
6. **Given** a list holding todos, **When** the list is deleted, **Then** the
   list and the todos it held are all gone, and requesting any of them gives a
   not-found answer.

---

### User Story 4 - Move a todo to another list (Priority: P3)

A consumer moves an existing todo out of the list it is in and into a different
existing list, without losing its title or status.

**Why this priority**: It is an explicit requirement, but it builds on lists and
todos already existing and can be delivered last without blocking anything else.

**Independent Test**: Create two lists and a todo in the first; move the todo to
the second; confirm it appears among the second list's todos, is absent from the
first list's todos, and kept its title and status.

**Acceptance Scenarios**:

1. **Given** a todo in list A and an existing list B, **When** the todo is moved
   to list B, **Then** it is returned as belonging to B with the same title and
   status.
2. **Given** the move above succeeded, **When** list A's todos are requested,
   **Then** the moved todo is not among them.
3. **Given** a todo in list A, **When** it is moved to a list that does not
   exist, **Then** a not-found answer is returned and the todo still belongs to
   list A.
4. **Given** a todo in list A, **When** it is moved to list A, **Then** the
   result is the unchanged todo still in list A.

### Edge Cases

- A todo is created with an empty or whitespace-only title: rejected as invalid
  input with a message naming the field, distinct from a not-found answer.
- A list is created with an empty or whitespace-only name: rejected the same way.
- Two lists are given the same name, or two todos the same title: allowed. Names
  and titles are labels, not identifiers.
- A list with no todos is asked for its todos: an empty collection is returned,
  which is a success, not a not-found answer.
- A todo is requested by an identifier that exists but under a different list
  than the one named in the request: treated as not found, so list membership
  cannot be bypassed.
- A list is deleted while it still holds todos: the todos are deleted with it.
- Titles and names containing non-ASCII characters (æ, ø, å) or leading and
  trailing spaces: stored and returned faithfully, with surrounding whitespace
  trimmed.
- Requests referring to an identifier of the wrong shape: rejected as invalid
  input rather than treated as a missing resource.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST let a consumer create a list by supplying a name, and
  MUST return the created list with a stable identifier assigned by the system.
- **FR-002**: System MUST let a consumer retrieve a single list by identifier,
  and retrieve all lists.
- **FR-003**: System MUST let a consumer change a list's name.
- **FR-004**: System MUST let a consumer delete a list.
- **FR-005**: System MUST let a consumer create a todo with a title inside a
  named existing list, and MUST store it as not done unless a status is given.
- **FR-006**: System MUST let a consumer retrieve a single todo by identifier.
- **FR-007**: System MUST let a consumer retrieve every todo belonging to a
  given list, and MUST return only that list's todos.
- **FR-008**: System MUST let a consumer change a todo's title, its done status,
  or both, leaving unmentioned fields unchanged.
- **FR-009**: System MUST let a consumer delete a todo.
- **FR-010**: System MUST let a consumer move a todo from its current list to
  another existing list, preserving the todo's identifier, title and status.
- **FR-011**: System MUST ensure every todo belongs to exactly one list at all
  times; a todo MUST NOT exist without a list.
- **FR-012**: System MUST answer any request naming a list or todo that does not
  exist with a clear not-found result that states which resource was missing,
  and MUST NOT fail, crash, or expose internal error detail.
- **FR-013**: System MUST keep serving subsequent requests normally after any
  not-found or invalid-input result.
- **FR-014**: System MUST reject a list name or todo title that is empty or only
  whitespace, with an invalid-input result distinguishable from not-found.
- **FR-015**: System MUST retain all lists and todos across a restart of the
  application, so that data created before a restart is readable after it.
- **FR-016**: System MUST delete the todos a list holds when that list is
  deleted, so no todo is left without a list.
- **FR-017**: System MUST treat a todo requested under a list it does not belong
  to as not found.
- **FR-018**: System MUST return, for every todo it hands back, which list the
  todo currently belongs to.

### Key Entities

- **List**: A named container for todos. Has a system-assigned identifier and a
  name supplied by the consumer. A list may hold zero or more todos. Names need
  not be unique.
- **Todo**: A single item of work. Has a system-assigned identifier, a title
  supplied by the consumer, a done/not-done status, and belongs to exactly one
  list. Titles need not be unique.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A consumer can go from nothing to a list holding a todo, and read
  that todo back, using three requests and no manual setup step.
- **SC-002**: All six required operations — create, read, change and delete for
  both lists and todos, plus reading a list's todos and moving a todo between
  lists — are reachable through the API, with 100% of them covered by a passing
  test.
- **SC-003**: Every operation, when aimed at a resource that does not exist,
  returns a not-found result naming the missing resource; zero such requests
  produce a crash, an unhandled failure, or an internal error response. This is
  verified for 100% of operations.
- **SC-004**: Data created before the application is stopped is 100% readable
  after it is started again, with identifiers, titles, statuses and list
  membership unchanged.
- **SC-005**: A reader can determine, from a todo returned by the API, which
  list it belongs to, without issuing a further request.

## Assumptions

- The consumer is another program or a developer exercising the API directly;
  there is no user interface, and no login, user accounts or permissions are in
  scope, since the brief mentions none.
- Deleting a list deletes the todos it holds. The brief requires both that lists
  be deletable and that every todo belong to a list; removing the todos is the
  only resolution that keeps both true. Refusing to delete a non-empty list was
  the alternative considered and rejected as more surprising.
- Identifiers are assigned by the system rather than supplied by the consumer,
  and are stable for the lifetime of the resource, including across a move
  between lists and across a restart.
- Lists and todos are returned in a stable, repeatable order; creation order is
  used, as the brief specifies no sorting.
- There is no pagination, filtering, searching or sorting beyond "the todos in
  this list", as none is mentioned in the brief.
- Volume is small — a single developer's lists, not a multi-tenant service — so
  no throughput or latency target is set beyond staying responsive.
- No audit trail, timestamps, soft deletes or history are kept; deletion is
  immediate and final.
- The service runs as a single application against a single data store; no
  replication or multi-instance coordination is assumed.
