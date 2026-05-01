<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\CoreProduct;
use Illuminate\Http\Request;

class CoreProductController extends Controller
{
    public function index()   { return response()->json(CoreProduct::withTrashed()->with('category')->paginate(100)); }
    public function show($id) { return response()->json(CoreProduct::withTrashed()->with(['category','stockEntrepots'])->findOrFail($id)); }

    public function store(Request $request)
    {
        $request->validate([
            'name'          => 'required|string',
            'enterprise_id' => 'nullable|uuid',
        ]);
        return response()->json(CoreProduct::create($request->all()), 201);
    }

    public function update(Request $request, $id)
    {
        $m = CoreProduct::withTrashed()->findOrFail($id);
        $m->update($request->all());
        return response()->json($m);
    }

    public function destroy($id)
    {
        CoreProduct::findOrFail($id)->delete();
        return response()->json(['message' => 'Supprimé.']);
    }
}
