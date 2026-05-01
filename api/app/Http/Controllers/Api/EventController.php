<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\EventClient;
use App\Models\EventService;
use App\Models\EventReservation;
use Illuminate\Http\Request;

class EventClientController extends Controller
{
    public function index()   { return response()->json(EventClient::withTrashed()->paginate(100)); }
    public function show($id) { return response()->json(EventClient::withTrashed()->with('reservations')->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(EventClient::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = EventClient::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { EventClient::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class EventServiceController extends Controller
{
    public function index()   { return response()->json(EventService::withTrashed()->paginate(100)); }
    public function show($id) { return response()->json(EventService::withTrashed()->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(EventService::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = EventService::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { EventService::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class EventReservationController extends Controller
{
    public function index(Request $r)
    {
        $q = EventReservation::withTrashed()->with(['client','user','services.service','produits.product','paiements']);
        if ($r->filled('pos_id')) $q->where('pos_id', $r->pos_id);
        if ($r->filled('statut')) $q->where('statut', $r->statut);
        return response()->json($q->latest('date_evenement')->paginate(50));
    }
    public function show($id) { return response()->json(EventReservation::withTrashed()->with(['client','user','services.service','produits.product','paiements.paymentMode'])->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(EventReservation::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = EventReservation::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { EventReservation::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}
