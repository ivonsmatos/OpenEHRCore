import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PractitionerForm from '../PractitionerForm';

// O formulário consulta a API de CBO via axios; mockamos para isolar o teste.
vi.mock('axios', () => ({
    default: {
        get: vi.fn(() => Promise.resolve({ data: { results: [] } })),
    },
}));

describe('PractitionerForm', () => {
    it('renders form fields correctly', () => {
        render(<PractitionerForm onSubmit={vi.fn()} onCancel={vi.fn()} />);

        expect(screen.getByText('Nome *')).toBeInTheDocument();
        expect(screen.getByText('Sobrenome *')).toBeInTheDocument();
        expect(screen.getByText(/Registro Profissional/)).toBeInTheDocument();
        expect(screen.getByText('Ocupação/Especialidade (CBO) *')).toBeInTheDocument();
        expect(screen.getByText('Salvar Profissional')).toBeInTheDocument();
        expect(screen.getByText('Cancelar')).toBeInTheDocument();
    });

    it('populates initial data', () => {
        const initialData = {
            family_name: 'Santos',
            given_names: ['Maria'],
            numero_conselho: '123456',
        } as any;
        render(<PractitionerForm onSubmit={vi.fn()} onCancel={vi.fn()} initialData={initialData} />);

        expect(screen.getByDisplayValue('Santos')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Maria')).toBeInTheDocument();
        expect(screen.getByDisplayValue('123456')).toBeInTheDocument();
    });

    it('validates required fields on submit', () => {
        const handleSubmit = vi.fn();
        render(<PractitionerForm onSubmit={handleSubmit} onCancel={vi.fn()} />);

        fireEvent.click(screen.getByText('Salvar Profissional'));

        expect(handleSubmit).not.toHaveBeenCalled();
        expect(screen.getByText('Nome é obrigatório')).toBeInTheDocument();
        expect(screen.getByText('Sobrenome é obrigatório')).toBeInTheDocument();
        expect(screen.getByText('Número do conselho é obrigatório')).toBeInTheDocument();
        expect(screen.getByText('Selecione uma ocupação/especialidade CBO')).toBeInTheDocument();
    });

    it('submits when required data is provided', async () => {
        const handleSubmit = vi.fn().mockResolvedValue(undefined);
        const initialData = {
            family_name: 'Santos',
            given_names: ['Maria'],
            numero_conselho: '123456',
            codigo_cbo: '225125',
        } as any;
        render(<PractitionerForm onSubmit={handleSubmit} onCancel={vi.fn()} initialData={initialData} />);

        fireEvent.click(screen.getByText('Salvar Profissional'));

        await waitFor(() => {
            expect(handleSubmit).toHaveBeenCalledTimes(1);
        });
        expect(handleSubmit).toHaveBeenCalledWith(expect.objectContaining({
            family_name: 'Santos',
            given_names: ['Maria'],
        }));
    });

    it('calls onCancel when cancel button is clicked', () => {
        const handleCancel = vi.fn();
        render(<PractitionerForm onSubmit={vi.fn()} onCancel={handleCancel} />);

        fireEvent.click(screen.getByText('Cancelar'));
        expect(handleCancel).toHaveBeenCalledTimes(1);
    });
});
