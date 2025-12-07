import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PractitionerCard from '../PractitionerCard';
import { Practitioner } from '../../../types/practitioner';

// Mock Practitioner Data
const mockPractitioner: Practitioner = {
    resourceType: 'Practitioner',
    id: '123',
    active: true,
    gender: 'male',
    birthDate: '1980-01-01',
    name: [{
        family: 'Silva',
        given: ['João', 'Carlos'],
        prefix: ['Dr.'],
        use: 'official'
    }],
    identifier: [{
        system: 'http://hl7.org.br/fhir/r4/NamingSystem/crm',
        value: 'CRM-SP-123456'
    }],
    qualification: [{
        code: {
            text: 'Cardiologia',
            coding: [{
                system: 'http://snomed.info/sct',
                code: 'Cardiology',
                display: 'Cardiologia'
            }]
        }
    }],
    telecom: [
        { system: 'phone', value: '(11) 99999-9999', use: 'work' },
        { system: 'email', value: 'joao.silva@hospital.com', use: 'work' }
    ]
};

describe('PractitionerCard', () => {
    it('renders practitioner name correctly', () => {
        render(<PractitionerCard practitioner={mockPractitioner} />);
        expect(screen.getByText('Dr. João Carlos Silva')).toBeInTheDocument();
    });

    it('renders CRM correctly', () => {
        render(<PractitionerCard practitioner={mockPractitioner} />);
        expect(screen.getByText('CRM-SP-123456')).toBeInTheDocument();
    });

    it('renders specialty correctly', () => {
        render(<PractitionerCard practitioner={mockPractitioner} />);
        expect(screen.getByText('Cardiologia')).toBeInTheDocument();
    });

    it('renders contact info correctly', () => {
        render(<PractitionerCard practitioner={mockPractitioner} />);
        expect(screen.getByText('(11) 99999-9999')).toBeInTheDocument();
        expect(screen.getByText('joao.silva@hospital.com')).toBeInTheDocument();
    });

    it('renders active status', () => {
        render(<PractitionerCard practitioner={mockPractitioner} />);
        expect(screen.getByText('Ativo')).toBeInTheDocument();
    });

    it('renders inactive status when active is false', () => {
        const inactivePractitioner = { ...mockPractitioner, active: false };
        render(<PractitionerCard practitioner={inactivePractitioner} />);
        expect(screen.getByText('Inativo')).toBeInTheDocument();
    });

    it('calls onClick handler when clicked', () => {
        const handleClick = vi.fn();
        render(<PractitionerCard practitioner={mockPractitioner} onClick={handleClick} />);

        // Click on the card container (div)
        // We can find it by text and go up, or add a test-id, or simplier: click the text
        fireEvent.click(screen.getByText('Dr. João Carlos Silva'));
        expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles missing optional fields gracefully', () => {
        const minimalPractitioner: Practitioner = {
            resourceType: 'Practitioner',
            id: '456',
            active: true,
            gender: 'female',
            birthDate: '1990-01-01',
            name: [{ given: ['Maria'], family: 'Fallback', use: 'official' }]
        };

        render(<PractitionerCard practitioner={minimalPractitioner} />);
        expect(screen.getByText(/Maria/)).toBeInTheDocument();
        expect(screen.getByText('Não especificado')).toBeInTheDocument(); // Specialty fallback
    });
});
