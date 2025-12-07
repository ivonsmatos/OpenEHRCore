import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PractitionerForm from '../PractitionerForm';

describe('PractitionerForm', () => {
    it('renders form fields correctly', () => {
        render(<PractitionerForm onSubmit={vi.fn()} onCancel={vi.fn()} />);

        expect(screen.getByText('Nome *')).toBeInTheDocument();
        expect(screen.getByText('Sobrenome *')).toBeInTheDocument();
        expect(screen.getByText('CRM *')).toBeInTheDocument();
        expect(screen.getByText('Salvar Profissional')).toBeInTheDocument();
        expect(screen.getByText('Cancelar')).toBeInTheDocument();
    });

    it('populates initial data', () => {
        const initialData = {
            family_name: 'Santos',
            given_names: ['Maria'],
            crm: 'CRM-SP-123456'
        };
        render(<PractitionerForm onSubmit={vi.fn()} onCancel={vi.fn()} initialData={initialData} />);

        expect(screen.getByDisplayValue('Santos')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Maria')).toBeInTheDocument();
        expect(screen.getByDisplayValue('CRM-SP-123456')).toBeInTheDocument();
    });

    it('validates required fields on submit', async () => {
        const handleSubmit = vi.fn();
        render(<PractitionerForm onSubmit={handleSubmit} onCancel={vi.fn()} />);

        fireEvent.click(screen.getByText('Salvar Profissional'));

        expect(handleSubmit).not.toHaveBeenCalled();
        expect(screen.getByText('Nome é obrigatório')).toBeInTheDocument();
        expect(screen.getByText('Sobrenome é obrigatório')).toBeInTheDocument();
        expect(screen.getByText('CRM é obrigatório')).toBeInTheDocument();
    });

    it('validates CRM format', async () => {
        const handleSubmit = vi.fn();
        render(<PractitionerForm onSubmit={handleSubmit} onCancel={vi.fn()} />); // Correção: onCancel deve ser função

        // Fill properly but invalid CRM
        fireEvent.change(screen.getByPlaceholderText('Ex: Maria da Silva'), { target: { value: 'Maria' } });
        fireEvent.change(screen.getByPlaceholderText('Ex: Santos'), { target: { value: 'Santos' } });
        fireEvent.change(screen.getByPlaceholderText('Ex: CRM-SP-123456'), { target: { value: 'INVALID-CRM' } });

        fireEvent.click(screen.getByText('Salvar Profissional'));

        expect(handleSubmit).not.toHaveBeenCalled();
        expect(screen.getByText(/Formato inválido/)).toBeInTheDocument();
    });

    it('submits form with valid data', async () => {
        const handleSubmit = vi.fn();
        render(<PractitionerForm onSubmit={handleSubmit} onCancel={vi.fn()} />);

        // Fill valid data
        fireEvent.change(screen.getByPlaceholderText('Ex: Maria da Silva'), { target: { value: 'Maria' } });
        fireEvent.change(screen.getByPlaceholderText('Ex: Santos'), { target: { value: 'Santos' } });
        fireEvent.change(screen.getByPlaceholderText('Ex: CRM-SP-123456'), { target: { value: 'CRM-SP-123456' } });
        fireEvent.change(screen.getByPlaceholderText('Ex: Cardiologia, Clínica Geral, etc.'), { target: { value: 'Cardiologia' } });

        fireEvent.click(screen.getByText('Salvar Profissional'));

        await waitFor(() => {
            expect(handleSubmit).toHaveBeenCalledTimes(1);
            expect(handleSubmit).toHaveBeenCalledWith(expect.objectContaining({
                family_name: 'Santos',
                given_names: ['Maria'],
                crm: 'CRM-SP-123456'
            }));
        });
    });

    it('calls onCancel when cancel button is clicked', () => {
        const handleCancel = vi.fn();
        render(<PractitionerForm onSubmit={vi.fn()} onCancel={handleCancel} />);

        fireEvent.click(screen.getByText('Cancelar'));
        expect(handleCancel).toHaveBeenCalledTimes(1);
    });
});
