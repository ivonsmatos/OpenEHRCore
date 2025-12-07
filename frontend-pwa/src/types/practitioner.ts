export interface Practitioner {
    id: string;
    resourceType: 'Practitioner';
    active: boolean;
    name: Array<{
        use: string;
        family: string;
        given: string[];
        prefix?: string[];
    }>;
    telecom?: Array<{
        system: string;
        value: string;
        use: string;
    }>;
    gender: 'male' | 'female' | 'other' | 'unknown';
    birthDate?: string;
    identifier?: Array<{
        system: string;
        value: string;
    }>;
    qualification?: Array<{
        code: {
            coding: Array<{
                system: string;
                code: string;
                display: string;
            }>;
            text: string;
        };
        identifier?: Array<{
            system: string;
            value: string;
        }>;
    }>;
}

export interface PractitionerRole {
    id: string;
    resourceType: 'PractitionerRole';
    active: boolean;
    practitioner: {
        reference: string;
        display?: string;
    };
    organization?: {
        reference: string;
        display?: string;
    };
    code?: Array<{
        coding: Array<{
            system: string;
            code: string;
            display: string;
        }>;
    }>;
    specialty?: Array<{
        coding: Array<{
            system: string;
            code: string;
            display: string;
        }>;
    }>;
    location?: Array<{
        reference: string;
    }>;
    availableTime?: Array<{
        daysOfWeek: string[];
        availableStartTime: string;
        availableEndTime: string;
    }>;
}

export interface PractitionerFormData {
    family_name: string;
    given_names: string[];
    prefix?: string;
    gender: 'male' | 'female' | 'other' | 'unknown';
    birthDate?: string;
    phone?: string;
    email?: string;
    crm: string;
    qualification_code: string;
    qualification_display: string;
}

export interface PractitionerFilters {
    name?: string;
    active?: boolean | null;
    specialty?: string;
}

export interface PractitionerListResponse {
    count: number;
    practitioners: Practitioner[];
}
