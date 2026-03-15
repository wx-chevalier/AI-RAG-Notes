import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'

describe('Sanity Check', () => {
    it('should verify 1+1=2', () => {
        expect(1 + 1).toBe(2)
    })

    it('should render a simple div', () => {
        render(<div data-testid="test">Hello</div>)
        expect(screen.getByTestId('test')).toHaveTextContent('Hello')
    })
})
