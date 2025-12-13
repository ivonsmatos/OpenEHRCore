/**
 * FHIR Resource Types
 */

export interface Resource {
    resourceType: string;
    id?: string;
    meta?: Meta;
}

export interface Meta {
    versionId?: string;
    lastUpdated?: string;
    source?: string;
    profile?: string[];
    security?: Coding[];
    tag?: Coding[];
}

export interface Coding {
    system?: string;
    version?: string;
    code?: string;
    display?: string;
    userSelected?: boolean;
}

export interface CodeableConcept {
    coding?: Coding[];
    text?: string;
}

export interface Reference {
    reference?: string;
    type?: string;
    identifier?: Identifier;
    display?: string;
}

export interface Identifier {
    use?: 'usual' | 'official' | 'temp' | 'secondary' | 'old';
    type?: CodeableConcept;
    system?: string;
    value?: string;
    period?: Period;
    assigner?: Reference;
}

export interface Period {
    start?: string;
    end?: string;
}

export interface HumanName {
    use?: 'usual' | 'official' | 'temp' | 'nickname' | 'anonymous' | 'old' | 'maiden';
    text?: string;
    family?: string;
    given?: string[];
    prefix?: string[];
    suffix?: string[];
    period?: Period;
}

export interface Address {
    use?: 'home' | 'work' | 'temp' | 'old' | 'billing';
    type?: 'postal' | 'physical' | 'both';
    text?: string;
    line?: string[];
    city?: string;
    district?: string;
    state?: string;
    postalCode?: string;
    country?: string;
    period?: Period;
}

export interface ContactPoint {
    system?: 'phone' | 'fax' | 'email' | 'pager' | 'url' | 'sms' | 'other';
    value?: string;
    use?: 'home' | 'work' | 'temp' | 'old' | 'mobile';
    rank?: number;
    period?: Period;
}

// Patient Resource
export interface Patient extends Resource {
    resourceType: 'Patient';
    identifier?: Identifier[];
    active?: boolean;
    name?: HumanName[];
    telecom?: ContactPoint[];
    gender?: 'male' | 'female' | 'other' | 'unknown';
    birthDate?: string;
    deceasedBoolean?: boolean;
    deceasedDateTime?: string;
    address?: Address[];
    maritalStatus?: CodeableConcept;
    multipleBirthBoolean?: boolean;
    multipleBirthInteger?: number;
    photo?: Attachment[];
    contact?: PatientContact[];
    communication?: PatientCommunication[];
    generalPractitioner?: Reference[];
    managingOrganization?: Reference;
    link?: PatientLink[];
}

export interface Attachment {
    contentType?: string;
    language?: string;
    data?: string;
    url?: string;
    size?: number;
    hash?: string;
    title?: string;
    creation?: string;
}

export interface PatientContact {
    relationship?: CodeableConcept[];
    name?: HumanName;
    telecom?: ContactPoint[];
    address?: Address;
    gender?: string;
    organization?: Reference;
    period?: Period;
}

export interface PatientCommunication {
    language: CodeableConcept;
    preferred?: boolean;
}

export interface PatientLink {
    other: Reference;
    type: 'replaced-by' | 'replaces' | 'refer' | 'seealso';
}

// Observation Resource
export interface Observation extends Resource {
    resourceType: 'Observation';
    identifier?: Identifier[];
    status: 'registered' | 'preliminary' | 'final' | 'amended' | 'corrected' | 'cancelled' | 'entered-in-error' | 'unknown';
    category?: CodeableConcept[];
    code: CodeableConcept;
    subject?: Reference;
    encounter?: Reference;
    effectiveDateTime?: string;
    effectivePeriod?: Period;
    issued?: string;
    performer?: Reference[];
    valueQuantity?: Quantity;
    valueCodeableConcept?: CodeableConcept;
    valueString?: string;
    valueBoolean?: boolean;
    valueInteger?: number;
    interpretation?: CodeableConcept[];
    note?: Annotation[];
    bodySite?: CodeableConcept;
    method?: CodeableConcept;
    referenceRange?: ObservationReferenceRange[];
    component?: ObservationComponent[];
}

export interface Quantity {
    value?: number;
    comparator?: '<' | '<=' | '>=' | '>';
    unit?: string;
    system?: string;
    code?: string;
}

export interface Annotation {
    authorReference?: Reference;
    authorString?: string;
    time?: string;
    text: string;
}

export interface ObservationReferenceRange {
    low?: Quantity;
    high?: Quantity;
    type?: CodeableConcept;
    appliesTo?: CodeableConcept[];
    age?: Range;
    text?: string;
}

export interface Range {
    low?: Quantity;
    high?: Quantity;
}

export interface ObservationComponent {
    code: CodeableConcept;
    valueQuantity?: Quantity;
    valueCodeableConcept?: CodeableConcept;
    valueString?: string;
    valueBoolean?: boolean;
    valueInteger?: number;
    interpretation?: CodeableConcept[];
    referenceRange?: ObservationReferenceRange[];
}

// Bundle Resource
export interface Bundle<T extends Resource = Resource> extends Resource {
    resourceType: 'Bundle';
    type: 'document' | 'message' | 'transaction' | 'transaction-response' | 'batch' | 'batch-response' | 'history' | 'searchset' | 'collection';
    total?: number;
    link?: BundleLink[];
    entry?: BundleEntry<T>[];
}

export interface BundleLink {
    relation: string;
    url: string;
}

export interface BundleEntry<T extends Resource = Resource> {
    fullUrl?: string;
    resource?: T;
    search?: BundleEntrySearch;
    request?: BundleEntryRequest;
    response?: BundleEntryResponse;
}

export interface BundleEntrySearch {
    mode?: 'match' | 'include' | 'outcome';
    score?: number;
}

export interface BundleEntryRequest {
    method: 'GET' | 'HEAD' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    url: string;
    ifNoneMatch?: string;
    ifModifiedSince?: string;
    ifMatch?: string;
    ifNoneExist?: string;
}

export interface BundleEntryResponse {
    status: string;
    location?: string;
    etag?: string;
    lastModified?: string;
    outcome?: Resource;
}

// Search Parameters
export interface SearchParams {
    [key: string]: string | number | boolean | undefined;
    _count?: number;
    _offset?: number;
    _sort?: string;
    _include?: string;
    _revinclude?: string;
    _summary?: 'true' | 'text' | 'data' | 'count' | 'false';
    _elements?: string;
}

// API Response Types
export interface ApiResponse<T> {
    data: T;
    status: number;
    headers: Record<string, string>;
}

export interface ApiError {
    message: string;
    status?: number;
    code?: string;
    details?: unknown;
}
