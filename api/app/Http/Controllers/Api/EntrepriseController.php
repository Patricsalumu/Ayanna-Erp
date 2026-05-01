<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Entreprise;
use Illuminate\Http\Request;

class EntrepriseController extends Controller
{
    public function index()
    {
        return response()->json(Entreprise::withTrashed()->latest()->paginate(50));
    }

    public function show($id)
    {
        return response()->json(Entreprise::withTrashed()->findOrFail($id));
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'id'            => 'nullable|uuid',
            'nom'           => 'required|string|max:255',
            'adresse'       => 'nullable|string',
            'telephone'     => 'nullable|string',
            'email'         => 'nullable|email',
            'logo'          => 'nullable|string',
            'devise'        => 'nullable|string',
            'pays'          => 'nullable|string',
            'secteur'       => 'nullable|string',
            'is_active'     => 'boolean',
        ]);

        $entreprise = Entreprise::create($data);
        return response()->json($entreprise, 201);
    }

    public function update(Request $request, $id)
    {
        $entreprise = Entreprise::withTrashed()->findOrFail($id);
        $entreprise->update($request->all());
        return response()->json($entreprise);
    }

    public function destroy($id)
    {
        Entreprise::findOrFail($id)->delete();
        return response()->json(['message' => 'Supprimé.']);
    }
}
